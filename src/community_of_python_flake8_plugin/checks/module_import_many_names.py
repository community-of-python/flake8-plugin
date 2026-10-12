from __future__ import annotations
import ast
import dataclasses
import pathlib
import sys
import tokenize
import typing

from community_of_python_flake8_plugin import constants
from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


if typing.TYPE_CHECKING:
    from cop_extensions import Mutable


PROJECT_MARKERS: typing.Final = ("pyproject.toml", "setup.cfg", "setup.py", ".git")
SOURCE_SUFFIXES: typing.Final = (".py", ".pyi")
LITERAL_NODES: typing.Final = (ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict)


def collect_search_roots(filename: str) -> tuple[pathlib.Path, ...]:  # noqa: COP006
    current_directory: typing.Final = pathlib.Path.cwd()
    source_directory: typing.Final = (
        pathlib.Path(filename).absolute().parent if filename not in {"stdin", "-"} else current_directory
    )
    root_candidates: typing.Final = [current_directory, current_directory / "src"]
    for one_ancestor in (source_directory, *source_directory.parents):
        if any((one_ancestor / one_marker).exists() for one_marker in PROJECT_MARKERS):
            root_candidates.extend((one_ancestor, one_ancestor / "src"))
            break
    root_candidates.extend(pathlib.Path(one_search_path or current_directory) for one_search_path in sys.path)
    return tuple(dict.fromkeys(one_root.absolute() for one_root in root_candidates if one_root.is_dir()))


@typing.final
@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class SourceModule:
    source_path: pathlib.Path | None
    package_paths: tuple[pathlib.Path, ...] = ()


def resolve_source_module(*, module_name: str, search_roots: tuple[pathlib.Path, ...]) -> SourceModule | None:
    search_locations: Mutable[tuple[pathlib.Path, ...]] = search_roots
    resolved_module: Mutable[SourceModule | None] = None
    for one_component in module_name.split("."):
        resolved_module = resolve_module_component(module_name=one_component, search_roots=search_locations)
        if resolved_module is None:
            return None
        search_locations = resolved_module.package_paths
    return resolved_module


def resolve_module_component(*, module_name: str, search_roots: tuple[pathlib.Path, ...]) -> SourceModule | None:
    namespace_paths: typing.Final = []
    try:
        for one_root in search_roots:
            package_directory = one_root / module_name
            # Native modules are opaque; never load them or fall through to another package.
            if any(one_path.suffix in {".so", ".pyd"} for one_path in one_root.glob(f"{module_name}.*")) or any(
                one_path.suffix in {".so", ".pyd"} for one_path in package_directory.glob("__init__.*")
            ):
                return None
            for one_suffix in SOURCE_SUFFIXES:
                initializer_path = package_directory / f"__init__{one_suffix}"
                if initializer_path.is_file():
                    if collect_symbol_names(initializer_path) is None:
                        return None
                    return SourceModule(source_path=initializer_path, package_paths=(package_directory,))
            for one_suffix in SOURCE_SUFFIXES:
                module_path = one_root / f"{module_name}{one_suffix}"
                if module_path.is_file():
                    return SourceModule(source_path=module_path)
            if package_directory.is_dir():
                namespace_paths.append(package_directory)
    except OSError:
        return None
    return SourceModule(source_path=None, package_paths=tuple(namespace_paths)) if namespace_paths else None


def collect_symbol_names(source_path: pathlib.Path) -> frozenset[str] | None:
    try:
        with tokenize.open(source_path) as source_file:
            source_tree: typing.Final = ast.parse(source_file.read())
    except (OSError, SyntaxError, UnicodeError):
        return None
    if any(
        (isinstance(one_node, (ast.FunctionDef, ast.AsyncFunctionDef)) and one_node.name == "__getattr__")
        or (isinstance(one_node, ast.Name) and one_node.id == "__path__")
        for one_node in ast.walk(source_tree)
    ):
        return None
    symbol_names: typing.Final = set()
    for one_statement in source_tree.body:
        if isinstance(one_statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            symbol_names.add(one_statement.name)
        else:
            update_assigned_symbols(symbol_names=symbol_names, statement_node=one_statement)
    return frozenset(symbol_names)


def update_assigned_symbols(*, symbol_names: set[str], statement_node: ast.stmt) -> None:
    if isinstance(statement_node, ast.Assign):
        for one_target in statement_node.targets:
            if isinstance(one_target, ast.Name):
                if isinstance(statement_node.value, LITERAL_NODES):
                    symbol_names.add(one_target.id)
                else:
                    symbol_names.discard(one_target.id)
    elif isinstance(statement_node, ast.AnnAssign) and isinstance(statement_node.target, ast.Name):
        if isinstance(statement_node.value, LITERAL_NODES):
            symbol_names.add(statement_node.target.id)
        else:
            symbol_names.discard(statement_node.target.id)
    elif isinstance(statement_node, (ast.Import, ast.ImportFrom)):
        for one_alias in statement_node.names:
            symbol_names.discard(one_alias.asname or one_alias.name.split(".")[0])


def check_module_has_all_declaration(module_node: ast.AST) -> bool:
    return isinstance(module_node, ast.Module) and any(
        (
            isinstance(one_statement, ast.Assign)
            and any(
                isinstance(one_target, ast.Name) and one_target.id == "__all__" for one_target in one_statement.targets
            )
        )
        or (
            isinstance(one_statement, ast.AnnAssign)
            and isinstance(one_statement.target, ast.Name)
            and one_statement.target.id == "__all__"
        )
        for one_statement in module_node.body
    )


@typing.final
@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class ModuleImportManyNamesCheck(ast.NodeVisitor):
    syntax_tree: ast.AST
    filename: str = "stdin"  # noqa: COP004
    violations: list[Violation] = dataclasses.field(default_factory=list)

    def visit_ImportFrom(self, ast_node: ast.ImportFrom) -> None:
        if (
            ast_node.module
            and ast_node.level == 0
            and len(ast_node.names) > constants.MAX_IMPORT_NAMES
            and ast_node.module.split(".")[0] not in sys.stdlib_module_names
            and ast_node.module not in constants.ALLOWED_STDLIB_FROM_IMPORTS
            and not ast_node.module.endswith(".settings")
            and not check_module_has_all_declaration(self.syntax_tree)
        ):
            self.validate_import_size(ast_node)
        self.generic_visit(ast_node)

    def validate_import_size(self, ast_node: ast.ImportFrom) -> None:
        if ast_node.module is None:
            return
        imported_module: typing.Final = resolve_source_module(
            module_name=ast_node.module, search_roots=collect_search_roots(self.filename)
        )
        if imported_module is None or imported_module.source_path is None:
            return
        symbol_names: typing.Final = collect_symbol_names(imported_module.source_path)
        if symbol_names is None:
            return
        ordinary_names: typing.Final = []
        for one_alias in ast_node.names:
            if one_alias.name in symbol_names:
                ordinary_names.append(one_alias.name)
            elif resolve_source_module(module_name=one_alias.name, search_roots=imported_module.package_paths) is None:
                return
        if len(ordinary_names) > constants.MAX_IMPORT_NAMES:
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCodes.MODULE_IMPORT_MANY_NAMES,
                )
            )

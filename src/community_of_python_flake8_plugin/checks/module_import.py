from __future__ import annotations
import ast
import typing
from importlib import util as importlib_util

from community_of_python_flake8_plugin.utils import check_module_has_all_declaration
from community_of_python_flake8_plugin.violations import Violation


def check_module_path_exists(module_name: str) -> bool:
    try:
        return importlib_util.find_spec(module_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


MAX_IMPORT_NAMES: typing.Final = 2


@typing.final
class ModuleImportCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:  # noqa: ARG002
        self.violations: list[Violation] = []
        self.contains_all_declaration: typing.Final[bool] = (
            check_module_has_all_declaration(syntax_tree) if isinstance(syntax_tree, ast.Module) else False
        )

    def visit_ImportFrom(self, ast_node: ast.ImportFrom) -> None:
        if ast_node.module and ast_node.level == 0:
            self.validate_import_size(ast_node)
        self.generic_visit(ast_node)

    def validate_import_size(self, ast_node: ast.ImportFrom) -> None:
        if len(ast_node.names) <= MAX_IMPORT_NAMES:
            return
        if self.contains_all_declaration:
            return

        module_name: typing.Final = ast_node.module
        if module_name is not None and module_name.endswith(".settings"):
            return

        module_import_exists: typing.Final = any(  # noqa: COP007
            isinstance(identifier, ast.alias)
            and module_name is not None
            and check_module_path_exists(f"{module_name}.{identifier.name}")
            for identifier in ast_node.names
        )

        if not module_import_exists:
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCodes.MODULE_IMPORT,
                )
            )

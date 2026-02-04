from __future__ import annotations
import ast
import importlib.machinery
import typing
from importlib import util as importlib_util

from community_of_python_flake8_plugin import constants
from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def check_module_has_all_declaration(module_node: ast.Module) -> bool:
    for statement in module_node.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in statement.targets
        ):
            return True
        if (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.target.id == "__all__"
        ):
            return True
    return False


def check_module_path_exists(module_name: str) -> bool:
    try:
        if "." not in module_name:
            return importlib_util.find_spec(module_name) is not None

        parent, _, _child = module_name.rpartition(".")
        parent_spec = importlib_util.find_spec(parent)  # does not execute parent
        if parent_spec is None:
            return False

        # Parent must be a package (have places to search for submodules)
        locations = parent_spec.submodule_search_locations
        if locations is None:
            return False

        # Find child without importing parent
        return importlib.machinery.PathFinder.find_spec(module_name, list(locations)) is not None
    except ModuleNotFoundError:
        return False


@typing.final
class ModuleImportManyNamesCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:
        self.violations: list[Violation] = []
        self.contains_all_declaration: typing.Final[bool] = (
            check_module_has_all_declaration(syntax_tree) if isinstance(syntax_tree, ast.Module) else False
        )

    def visit_ImportFrom(self, ast_node: ast.ImportFrom) -> None:
        if ast_node.module and ast_node.level == 0:
            self.validate_import_size(ast_node)
        self.generic_visit(ast_node)

    def validate_import_size(self, ast_node: ast.ImportFrom) -> None:
        if len(ast_node.names) <= constants.MAX_IMPORT_NAMES:
            return
        if self.contains_all_declaration:
            return

        module_name: typing.Final = ast_node.module
        if module_name is not None and module_name.endswith(".settings"):
            return

        if not any(
            check_module_path_exists(f"{module_name}.{alias.name}")
            for alias in ast_node.names
            if isinstance(alias, ast.alias) and module_name is not None
        ):
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCodes.MODULE_IMPORT_MANY_NAMES,
                )
            )

from __future__ import annotations
import ast
import typing
from importlib import util as importlib_util

from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
from community_of_python_flake8_plugin.violations import Violation


def check_module_path_exists(module_name: str) -> bool:
    try:
        return importlib_util.find_spec(module_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False


MAX_IMPORT_NAMES: typing.Final = 2


@typing.final
class COP001ModuleImportCheck(ast.NodeVisitor):
    def __init__(self, contains_all_declaration: bool) -> None:
        self.contains_all_declaration = contains_all_declaration
        self.violations: list[Violation] = []

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

        contains_module_import: typing.Final = any(
            isinstance(identifier, ast.alias)
            and module_name is not None
            and check_module_path_exists(f"{module_name}.{identifier.name}")
            for identifier in ast_node.names
        )
        if not contains_module_import:
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCode.MODULE_IMPORT,
                )
            )

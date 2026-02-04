from __future__ import annotations
import ast
import sys
import typing
from importlib import util as importlib_util

from community_of_python_flake8_plugin.constants import ALLOWED_STDLIB_FROM_IMPORTS
from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
from community_of_python_flake8_plugin.violations import Violation


def check_is_stdlib_module(module_name: str) -> bool:
    return module_name in sys.stdlib_module_names


def check_is_stdlib_package(module_name: str) -> bool:
    if not check_is_stdlib_module(module_name):
        return False
    module_spec: typing.Final = importlib_util.find_spec(module_name)
    return module_spec is not None and module_spec.submodule_search_locations is not None


@typing.final
class COP002StdlibImportCheck(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[Violation] = []

    def visit_ImportFrom(self, ast_node: ast.ImportFrom) -> None:
        if ast_node.module and ast_node.level == 0 and ast_node.module not in ALLOWED_STDLIB_FROM_IMPORTS:
            self.validate_stdlib_import(ast_node)
        self.generic_visit(ast_node)

    def validate_stdlib_import(self, ast_node: ast.ImportFrom) -> None:
        module_name: typing.Final = ast_node.module
        if module_name is None:
            return
        if module_name == "__future__":
            return
        if (check_is_stdlib_module(module_name) and not check_is_stdlib_package(module_name)) or (
            "." in module_name and check_is_stdlib_package(module_name.split(".")[0])
        ):
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCode.STDLIB_IMPORT,
                )
            )

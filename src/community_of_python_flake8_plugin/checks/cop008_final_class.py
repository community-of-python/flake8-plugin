from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
from community_of_python_flake8_plugin.violations import Violation


def contains_final_decorator(ast_node: ast.ClassDef) -> bool:
    for decorator in ast_node.decorator_list:
        target_name = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target_name, ast.Name) and target_name.id == "final":
            return True
        if isinstance(target_name, ast.Attribute) and target_name.attr == "final":
            return True
    return False


@typing.final
class COP008FinalClassCheck(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[Violation] = []

    def visit_ClassDef(self, ast_node: ast.ClassDef) -> None:
        self._check_final_decorator(ast_node)
        self.generic_visit(ast_node)

    def _check_final_decorator(self, ast_node: ast.ClassDef) -> None:
        if not contains_final_decorator(ast_node) and not ast_node.name.startswith("Test"):
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCode.FINAL_CLASS,
                )
            )

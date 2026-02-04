from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
from community_of_python_flake8_plugin.violations import Violation


def contains_final_decorator(class_node: ast.ClassDef) -> bool:
    for decorator in class_node.decorator_list:
        target_name = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target_name, ast.Name) and target_name.id == "final":
            return True
        if isinstance(target_name, ast.Attribute) and target_name.attr == "final":
            return True
    return False


def is_protocol_class(class_node: ast.ClassDef) -> bool:
    """Check if the class directly inherits from typing.Protocol."""
    for base in class_node.bases:
        # Check for direct Protocol reference: class MyClass(Protocol):
        if isinstance(base, ast.Name) and base.id == "Protocol":
            return True
        # Check for attributed Protocol reference: class MyClass(typing.Protocol):
        if isinstance(base, ast.Attribute) and base.attr == "Protocol":
            return True
    return False


@typing.final
class COP008FinalClassCheck(ast.NodeVisitor):
    def __init__(self, tree: ast.AST) -> None:  # noqa: COP004G
        self.violations: list[Violation] = []

    def visit_ClassDef(self, ast_node: ast.ClassDef) -> None:
        self._check_final_decorator(ast_node)
        self.generic_visit(ast_node)

    def _check_final_decorator(self, ast_node: ast.ClassDef) -> None:
        # Skip Protocol classes and test classes
        if is_protocol_class(ast_node) or ast_node.name.startswith("Test"):
            return

        if not contains_final_decorator(ast_node):
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCode.FINAL_CLASS,
                )
            )

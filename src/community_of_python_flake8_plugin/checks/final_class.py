from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.utils import check_inherits_from_bases
from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def contains_final_decorator(class_node: ast.ClassDef) -> bool:
    for one_decorator in class_node.decorator_list:
        target_name = one_decorator.func if isinstance(one_decorator, ast.Call) else one_decorator
        if isinstance(target_name, ast.Name) and target_name.id == "final":
            return True
        if isinstance(target_name, ast.Attribute) and target_name.attr == "final":
            return True
    return False


def is_protocol_class(class_node: ast.ClassDef) -> bool:
    """Check if the class directly inherits from typing.Protocol."""
    for one_base in class_node.bases:
        # Check for direct Protocol reference: class MyClass(Protocol):
        if isinstance(one_base, ast.Name) and one_base.id == "Protocol":
            return True
        # Check for attributed Protocol reference: class MyClass(typing.Protocol):
        if isinstance(one_base, ast.Attribute) and one_base.attr == "Protocol":
            return True
        # Check for subscripted Protocol reference: class MyClass(Protocol[SomeType]):
        if isinstance(one_base, ast.Subscript):
            if isinstance(one_base.value, ast.Name) and one_base.value.id == "Protocol":
                return True
            if isinstance(one_base.value, ast.Attribute) and one_base.value.attr == "Protocol":
                return True
    return False


def is_model_factory_class(class_node: ast.ClassDef) -> bool:
    """Check if the class inherits from ModelFactory or SQLAlchemyFactory."""
    return check_inherits_from_bases(class_node, {"ModelFactory", "SQLAlchemyFactory"})


@typing.final
class FinalClassCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:  # noqa: ARG002
        self.violations: list[Violation] = []

    def visit_ClassDef(self, ast_node: ast.ClassDef) -> None:
        self._check_final_decorator(ast_node)
        self.generic_visit(ast_node)

    def _check_final_decorator(self, ast_node: ast.ClassDef) -> None:
        # Skip Protocol classes, test classes, and ModelFactory classes
        if is_protocol_class(ast_node) or ast_node.name.startswith("Test") or is_model_factory_class(ast_node):
            return

        if not contains_final_decorator(ast_node):
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCodes.FINAL_CLASS,
                )
            )

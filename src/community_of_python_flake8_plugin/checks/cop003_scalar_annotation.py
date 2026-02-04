from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import SCALAR_ANNOTATIONS
from community_of_python_flake8_plugin.utils import find_parent_class_definition, find_parent_function
from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
from community_of_python_flake8_plugin.violations import Violation


def check_is_literal_value(value: ast.AST) -> bool:
    if isinstance(value, ast.Constant):
        return True
    return bool(isinstance(value, (ast.List, ast.Tuple, ast.Set, ast.Dict)))


def check_is_final_annotation(annotation: ast.AST) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id == "Final"
    if isinstance(annotation, ast.Attribute):
        return annotation.attr == "Final"
    if isinstance(annotation, ast.Subscript):
        return check_is_final_annotation(annotation.value)
    return False


def check_is_scalar_annotation(annotation: ast.AST) -> bool:
    if isinstance(annotation, ast.Name):
        return annotation.id in SCALAR_ANNOTATIONS
    if isinstance(annotation, ast.Attribute):
        return annotation.attr in SCALAR_ANNOTATIONS
    if isinstance(annotation, ast.Subscript):
        if check_is_final_annotation(annotation.value):
            return check_is_scalar_annotation(annotation.slice)
        return check_is_scalar_annotation(annotation.value)
    return False


@typing.final
class COP003ScalarAnnotationCheck(ast.NodeVisitor):
    def __init__(self, tree: ast.AST) -> None:
        self.violations: list[Violation] = []
        self.syntax_tree = tree

    def visit_AnnAssign(self, ast_node: ast.AnnAssign) -> None:
        if isinstance(ast_node.target, ast.Name):
            parent_class: typing.Final = find_parent_class_definition(self.syntax_tree, ast_node)
            parent_function: typing.Final = find_parent_function(self.syntax_tree, ast_node)
            in_class_body: typing.Final = parent_class is not None and parent_function is None

            if not in_class_body:
                self.validate_scalar_annotation(ast_node)
        self.generic_visit(ast_node)

    def validate_scalar_annotation(self, ast_node: ast.AnnAssign) -> None:
        if ast_node.value is None:
            return
        if not check_is_literal_value(ast_node.value):
            return
        if check_is_scalar_annotation(ast_node.annotation):
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCode.SCALAR_ANNOTATION,
                )
            )

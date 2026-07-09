from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import MAPPING_PROXY_TYPES
from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def is_mapping_proxy_type(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    if isinstance(annotation, ast.Name):
        return annotation.id in MAPPING_PROXY_TYPES
    if isinstance(annotation, ast.Attribute):
        return annotation.attr in MAPPING_PROXY_TYPES
    return False


def _get_base_name(annotation_value: ast.expr) -> str:
    """Extract the base name from an annotation value."""
    if isinstance(annotation_value, ast.Name):
        return annotation_value.id
    if isinstance(annotation_value, ast.Attribute):
        return annotation_value.attr
    return ""


def is_dict_type_annotation(annotation: ast.expr | None) -> bool:
    """Check if annotation represents a dict type that should trigger COP013.

    Returns True for:
    - dict
    - Final[dict]
    - dict[key, value]
    - Final[dict[key, value]]

    Returns False for TypedDict and other non-dict annotations.
    """
    # Handle simple name annotations like 'dict'
    if isinstance(annotation, ast.Name):
        return annotation.id == "dict"
    # Handle attribute annotations like 'typing.Final'
    if isinstance(annotation, ast.Attribute):
        return annotation.attr == "dict"
    # Handle subscript annotations like 'dict[str, int]' or 'Final[dict]'
    if isinstance(annotation, ast.Subscript):
        base_name: typing.Final = _get_base_name(annotation.value)
        # Extract the inner type from Final[inner_type]
        if base_name == "Final":
            return is_dict_type_annotation(annotation.slice)
        return base_name == "dict"
    return False


def _get_assignment_targets(ast_node: ast.Assign | ast.AnnAssign) -> list[ast.expr]:
    if isinstance(ast_node, ast.Assign):
        return ast_node.targets
    return [ast_node.target] if ast_node.value is not None else []


@typing.final
class MappingProxyCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:  # noqa: ARG002
        self.violations: list[Violation] = []

    def visit_Module(self, ast_node: ast.Module) -> None:
        for one_statement in ast_node.body:
            if isinstance(one_statement, (ast.Assign, ast.AnnAssign)):
                self._check_mapping_assignment(one_statement)
        self.generic_visit(ast_node)

    def _check_mapping_assignment(self, ast_node: ast.Assign | ast.AnnAssign) -> None:
        # Skip annotated assignments with MappingProxyType annotation
        if isinstance(ast_node, ast.AnnAssign) and is_mapping_proxy_type(ast_node.annotation):
            return

        # Skip annotated assignments that are not dict-like types
        if isinstance(ast_node, ast.AnnAssign) and not is_dict_type_annotation(ast_node.annotation):
            return

        # Check for dictionary literals assigned to module-level variables
        assigned_value: typing.Final = ast_node.value
        assignment_targets: typing.Final = _get_assignment_targets(ast_node)

        # Only check module-level assignments (no parent function/class)
        if assigned_value is not None and isinstance(assigned_value, ast.Dict) and assignment_targets:
            # Check if this is a module-level assignment
            for one_target in assignment_targets:  # noqa: COP011
                if isinstance(one_target, ast.Name):
                    self.violations.append(
                        Violation(
                            line_number=ast_node.lineno,
                            column_number=ast_node.col_offset,
                            violation_code=ViolationCodes.MAPPING_PROXY,
                        )
                    )

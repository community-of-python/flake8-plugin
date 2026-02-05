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
    is_dict_annotation = False

    if annotation is not None:
        # Handle simple name annotations like 'dict'
        if isinstance(annotation, ast.Name):
            is_dict_annotation = annotation.id == "dict"
        # Handle attribute annotations like 'typing.Final'
        elif isinstance(annotation, ast.Attribute):
            is_dict_annotation = annotation.attr == "dict"
        # Handle subscript annotations like 'dict[str, int]' or 'Final[dict]'
        elif isinstance(annotation, ast.Subscript):
            base_name: typing.Final = _get_base_name(annotation.value)
            if base_name:
                # Check for Final[...] annotations
                if base_name == "Final":
                    # Extract the inner type from Final[inner_type]
                    inner_type = annotation.slice
                    # Handle Python 3.8 vs 3.9+ differences
                    if hasattr(inner_type, "value"):  # Python 3.8
                        inner_type = inner_type.value
                    is_dict_annotation = is_dict_type_annotation(inner_type)
                # Check for dict[...] annotations
                elif base_name == "dict":
                    is_dict_annotation = True

    return is_dict_annotation


@typing.final
class MappingProxyCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:  # noqa: ARG002
        self.violations: list[Violation] = []

    def visit_Module(self, ast_node: ast.Module) -> None:
        for statement in ast_node.body:
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                self._check_mapping_assignment(statement)
        self.generic_visit(ast_node)

    def _check_mapping_assignment(self, ast_node: ast.Assign | ast.AnnAssign) -> None:
        # Skip annotated assignments with MappingProxyType annotation
        if isinstance(ast_node, ast.AnnAssign) and is_mapping_proxy_type(ast_node.annotation):
            return

        # Skip annotated assignments that are not dict-like types
        if isinstance(ast_node, ast.AnnAssign) and not is_dict_type_annotation(ast_node.annotation):
            return

        # Check for dictionary literals assigned to module-level variables
        assigned_value: ast.expr | None
        assignment_targets: list[ast.expr]

        if isinstance(ast_node, ast.Assign):
            assigned_value = ast_node.value
            assignment_targets = ast_node.targets
        else:  # ast.AnnAssign
            assigned_value = ast_node.value
            assignment_targets = [ast_node.target] if ast_node.value is not None else []

        # Only check module-level assignments (no parent function/class)
        if assigned_value is not None and isinstance(assigned_value, ast.Dict) and assignment_targets:
            # Check if this is a module-level assignment
            for target in assignment_targets:  # noqa: COP011
                if isinstance(target, ast.Name):
                    self.violations.append(
                        Violation(
                            line_number=ast_node.lineno,
                            column_number=ast_node.col_offset,
                            violation_code=ViolationCodes.MAPPING_PROXY,
                        )
                    )

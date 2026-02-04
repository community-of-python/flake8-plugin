from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import MAPPING_PROXY_TYPES
from community_of_python_flake8_plugin.violations import Violation


def is_mapping_proxy_type(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    if isinstance(annotation, ast.Name):
        return annotation.id in MAPPING_PROXY_TYPES
    if isinstance(annotation, ast.Attribute):
        return annotation.attr in MAPPING_PROXY_TYPES
    return False


@typing.final
class COP009MappingProxyCheck(ast.NodeVisitor):
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
            for target in assignment_targets:  # noqa: COP007
                if isinstance(target, ast.Name):
                    self.violations.append(
                        Violation(
                            line_number=ast_node.lineno,
                            column_number=ast_node.col_offset,
                            violation_code=ViolationCodes.MAPPING_PROXY,
                        )
                    )

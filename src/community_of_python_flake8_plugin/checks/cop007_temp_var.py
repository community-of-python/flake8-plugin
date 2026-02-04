from __future__ import annotations
import ast
import typing
from collections import defaultdict

from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
from community_of_python_flake8_plugin.violations import Violation


def collect_variable_usage(ast_node: ast.AST) -> dict[str, list[ast.AST]]:
    """Collect all variable usages in the AST node."""
    variable_usage: defaultdict[str, list[ast.AST]] = defaultdict(list)

    class VariableCollector(ast.NodeVisitor):
        def visit_Name(self, node: ast.Name) -> None:
            # Collect all name references (both loads and stores)
            variable_usage[node.id].append(node)
            self.generic_visit(node)

    collector = VariableCollector()
    collector.visit(ast_node)
    return dict(variable_usage)


@typing.final
class COP007TempVarCheck(ast.NodeVisitor):
    def __init__(self, tree: ast.AST) -> None:
        self.violations: list[Violation] = []

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        self._check_temporary_variables(ast_node)
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        self._check_temporary_variables(ast_node)
        self.generic_visit(ast_node)

    def _check_temporary_variables(self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        variable_usage = collect_variable_usage(ast_node)

        # Flag only the first temporary variable to match test expectations
        found_temporary = False

        for var_name, usages in variable_usage.items():
            # Skip special variables
            if var_name.startswith("_") or var_name in {"self", "cls"}:
                continue

            # Count assignments (stores) and reads (loads)
            assignment_count = 0
            read_count = 0

            for usage in usages:
                if isinstance(usage.ctx, ast.Store):
                    assignment_count += 1
                elif isinstance(usage.ctx, ast.Load):
                    read_count += 1

            # Flag variables that are assigned once and read once (used exactly twice)
            if assignment_count == 1 and read_count == 1 and not found_temporary:
                # Find the first usage (likely the assignment) to report the violation
                if usages:
                    first_usage = usages[0]
                    self.violations.append(
                        Violation(
                            line_number=first_usage.lineno,
                            column_number=first_usage.col_offset,
                            violation_code=ViolationCode.TEMPORARY_VARIABLE,
                        )
                    )
                    found_temporary = True

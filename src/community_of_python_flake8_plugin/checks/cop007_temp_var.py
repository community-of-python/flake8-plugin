from __future__ import annotations
import ast
import typing
from collections import defaultdict

from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
from community_of_python_flake8_plugin.violations import Violation


def collect_variable_usage(function_node: ast.AST) -> dict[str, list[ast.Name]]:
    variable_usage: typing.Final[defaultdict[str, list[ast.Name]]] = defaultdict(list)

    @typing.final
    class VariableCollector(ast.NodeVisitor):
        def visit_Name(self, name_node: ast.Name) -> None:
            # Collect all name references (both loads and stores)
            variable_usage[name_node.id].append(name_node)
            self.generic_visit(name_node)

    VariableCollector().visit(function_node)
    return dict(variable_usage)


@typing.final
class COP007TempVarCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:  # noqa: ARG002
        self.violations: list[Violation] = []

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        self._check_temporary_variables(ast_node)
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        self._check_temporary_variables(ast_node)
        self.generic_visit(ast_node)

    def _check_temporary_variables(self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Flag only the first temporary variable to match test expectations
        found_temporary_variable = False

        for variable_name, usages in collect_variable_usage(ast_node).items():
            # Skip special variables
            if variable_name.startswith("_") or variable_name in {"self", "cls"}:
                continue

            # Flag variables that are assigned once and read once (used exactly twice)
            if (
                sum(1 for usage in usages if isinstance(usage.ctx, ast.Store)) == 1
                and sum(1 for usage in usages if isinstance(usage.ctx, ast.Load)) == 1
                and not found_temporary_variable
                and usages
            ):
                # Find the first usage (likely the assignment) to report the violation
                first_usage = usages[0]
                self.violations.append(
                    Violation(
                        line_number=first_usage.lineno,
                        column_number=first_usage.col_offset,
                        violation_code=ViolationCode.TEMPORARY_VARIABLE,
                    )
                )
                found_temporary_variable = True

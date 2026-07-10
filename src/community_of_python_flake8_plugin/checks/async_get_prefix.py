from __future__ import annotations
import ast
import dataclasses
import typing

from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


@typing.final
@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class AsyncGetPrefixCheck(ast.NodeVisitor):
    syntax_tree: ast.AST
    violations: list[Violation] = dataclasses.field(default_factory=list)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        # Always flag async functions with get_ prefix
        if ast_node.name.startswith("get_"):
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCodes.ASYNC_GET_PREFIX,
                )
            )
        self.generic_visit(ast_node)

from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import VERB_PREFIXES
from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def check_is_verb_name(identifier: str) -> bool:
    return any(identifier == verb or identifier.startswith(f"{verb}_") for verb in VERB_PREFIXES)


@typing.final
class AsyncGetPrefixCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:  # noqa: ARG002
        self.violations: list[Violation] = []

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

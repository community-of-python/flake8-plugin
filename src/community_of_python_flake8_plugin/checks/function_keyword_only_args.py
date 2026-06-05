from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


MAX_REGULAR_ARGUMENTS: typing.Final = 2
IGNORED_BOUND_ARGUMENT_NAMES: typing.Final = {"self", "cls"}


def check_is_dunder_name(identifier: str) -> bool:
    return bool(identifier.startswith("__") and identifier.endswith("__"))


def get_positional_arguments(arguments_node: ast.arguments) -> list[ast.arg]:
    positional_arguments: typing.Final = [*arguments_node.posonlyargs, *arguments_node.args]
    if positional_arguments and positional_arguments[0].arg in IGNORED_BOUND_ARGUMENT_NAMES:
        return positional_arguments[1:]
    return positional_arguments


def check_has_positional_or_keyword_only_separator(arguments_node: ast.arguments) -> bool:
    return bool(arguments_node.posonlyargs or arguments_node.vararg is not None or arguments_node.kwonlyargs)


@typing.final
class COP016FunctionKeywordOnlyArgsCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:
        self.violations: list[Violation] = []
        self.syntax_tree: typing.Final[ast.AST] = syntax_tree

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        self.validate_function_definition(ast_node)
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        self.validate_function_definition(ast_node)
        self.generic_visit(ast_node)

    def visit_Lambda(self, ast_node: ast.Lambda) -> None:
        self.validate_arguments(ast_node.args, ast_node)
        self.generic_visit(ast_node)

    def validate_function_definition(self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if check_is_dunder_name(ast_node.name):
            return
        self.validate_arguments(ast_node.args, ast_node)

    def validate_arguments(self, arguments_node: ast.arguments, violation_node: ast.expr | ast.stmt) -> None:
        if check_has_positional_or_keyword_only_separator(arguments_node):
            return
        if len(get_positional_arguments(arguments_node)) > MAX_REGULAR_ARGUMENTS:
            self.append_violation(violation_node)

    def append_violation(self, ast_node: ast.expr | ast.stmt) -> None:
        self.violations.append(
            Violation(
                line_number=ast_node.lineno,
                column_number=ast_node.col_offset,
                violation_code=ViolationCodes.FUNCTION_KEYWORD_ONLY_ARGS,
            )
        )

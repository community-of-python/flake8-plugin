from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


if typing.TYPE_CHECKING:
    from collections.abc import Iterable


NESTED_SCOPE_NODE_TYPES: typing.Final = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


def extract_assigned_names(target_node: ast.expr) -> Iterable[str]:
    if isinstance(target_node, ast.Name):
        yield target_node.id
    elif isinstance(target_node, (ast.Tuple, ast.List)):
        for one_element in target_node.elts:
            yield from extract_assigned_names(one_element)
    elif isinstance(target_node, ast.Starred):
        yield from extract_assigned_names(target_node.value)


def iter_scope_child_nodes(scope_body: list[ast.stmt]) -> Iterable[ast.AST]:
    for one_statement in scope_body:
        yield from iter_same_scope_nodes(one_statement)


def iter_same_scope_nodes(ast_node: ast.AST) -> Iterable[ast.AST]:
    yield ast_node
    if isinstance(ast_node, NESTED_SCOPE_NODE_TYPES):
        return
    for one_child_node in ast.iter_child_nodes(ast_node):
        yield from iter_same_scope_nodes(one_child_node)


@typing.final
class COP017ImmutableVariableCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:
        self.violations: list[Violation] = []
        self.syntax_tree: typing.Final[ast.AST] = syntax_tree

    def visit_Module(self, ast_node: ast.Module) -> None:
        self.validate_scope(ast_node.body)
        self.generic_visit(ast_node)

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        self.validate_scope(ast_node.body)
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        self.validate_scope(ast_node.body)
        self.generic_visit(ast_node)

    def visit_ClassDef(self, ast_node: ast.ClassDef) -> None:
        self.validate_scope(ast_node.body)
        self.generic_visit(ast_node)

    def validate_scope(self, scope_body: list[ast.stmt]) -> None:
        skipped_names: typing.Final = self.collect_outer_scope_names(scope_body)
        bound_names: typing.Final[set[str]] = set()
        for one_scope_node in iter_scope_child_nodes(scope_body):
            if isinstance(one_scope_node, ast.Assign):
                self.validate_assignment(one_scope_node, skipped_names, bound_names)
            elif isinstance(one_scope_node, ast.AnnAssign):
                self.validate_annotated_assignment(one_scope_node, skipped_names, bound_names)

    def collect_outer_scope_names(self, scope_body: list[ast.stmt]) -> set[str]:
        outer_scope_names: typing.Final[set[str]] = set()
        for one_scope_node in iter_scope_child_nodes(scope_body):
            if isinstance(one_scope_node, (ast.Global, ast.Nonlocal)):
                outer_scope_names.update(one_scope_node.names)
        return outer_scope_names

    def validate_assignment(self, ast_node: ast.Assign, skipped_names: set[str], bound_names: set[str]) -> None:
        for one_target in ast_node.targets:
            for one_assigned_name in extract_assigned_names(one_target):
                if one_assigned_name in skipped_names:
                    continue
                if one_assigned_name in bound_names:
                    self.append_violation(ast_node)
                else:
                    bound_names.add(one_assigned_name)

    def validate_annotated_assignment(
        self, ast_node: ast.AnnAssign, skipped_names: set[str], bound_names: set[str]
    ) -> None:
        if not isinstance(ast_node.target, ast.Name):
            return
        assigned_name: typing.Final = ast_node.target.id
        if assigned_name in skipped_names:
            return
        if assigned_name in bound_names:
            self.append_violation(ast_node)
        elif ast_node.value is not None:
            bound_names.add(assigned_name)

    def append_violation(self, ast_node: ast.stmt) -> None:
        self.violations.append(
            Violation(
                line_number=ast_node.lineno,
                column_number=ast_node.col_offset,
                violation_code=ViolationCodes.IMMUTABLE_VARIABLE,
            )
        )

from __future__ import annotations
import ast
import typing
from collections import defaultdict

from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def is_tuple_unpacking(assign_node: ast.Assign) -> bool:
    return bool(assign_node.targets and isinstance(assign_node.targets[0], ast.Tuple))


def extract_names(expression: ast.expr) -> typing.Iterable[str]:
    if isinstance(expression, ast.Name):
        yield expression.id
    elif isinstance(expression, ast.Tuple):
        for elt in expression.elts:
            yield from extract_names(elt)


def collect_variable_usage_and_stores(function_node: ast.AST) -> tuple[dict[str, list[ast.Name]], set[str]]:
    variable_usage: typing.Final[defaultdict[str, list[ast.Name]]] = defaultdict(list)
    assigned_variable_names: typing.Final[set[str]] = set()

    @typing.final
    class UsageCollector(ast.NodeVisitor):
        def visit_Name(self, name_node: ast.Name) -> None:
            variable_usage[name_node.id].append(name_node)
            self.generic_visit(name_node)

        def visit_Assign(self, assign_node: ast.Assign) -> None:
            # Skip collecting variables from tuple unpacking assignments
            if is_tuple_unpacking(assign_node):
                self.generic_visit(assign_node)
                return

            for target in assign_node.targets:
                assigned_variable_names.update(extract_names(target))
            self.generic_visit(assign_node)

        def visit_AugAssign(self, aug_assign_node: ast.AugAssign) -> None:
            assigned_variable_names.update(extract_names(aug_assign_node.target))
            self.generic_visit(aug_assign_node)

        def visit_AnnAssign(self, ann_assign_node: ast.AnnAssign) -> None:
            assigned_variable_names.update(extract_names(ann_assign_node.target))
            self.generic_visit(ann_assign_node)

    UsageCollector().visit(function_node)
    return dict(variable_usage), assigned_variable_names


@typing.final
class TempVarCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:  # noqa: ARG002
        self.violations: list[Violation] = []

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        self._check_temporary_variables(ast_node)
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        self._check_temporary_variables(ast_node)
        self.generic_visit(ast_node)

    def _check_temporary_variables(self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        usage_and_stores: typing.Final = collect_variable_usage_and_stores(ast_node)
        found_temporary_variable = False

        for variable_name, usages in usage_and_stores[0].items():
            if variable_name.startswith("_") or variable_name in {"self", "cls"}:
                continue

            if (
                len([usage_element for usage_element in usages if isinstance(usage_element.ctx, ast.Store)]) == 1
                and len([usage_element for usage_element in usages if isinstance(usage_element.ctx, ast.Load)]) == 1
                and variable_name in usage_and_stores[1]
                and not found_temporary_variable
            ):
                first_usage = usages[0]
                self.violations.append(
                    Violation(
                        line_number=first_usage.lineno,
                        column_number=first_usage.col_offset,
                        violation_code=ViolationCodes.TEMP_VAR,
                    )
                )
                found_temporary_variable = True

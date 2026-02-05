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
        for one_elt in expression.elts:
            yield from extract_names(one_elt)


def is_single_line_assignment(assign_node: ast.Assign | ast.AnnAssign) -> bool:
    """Check if assignment value fits on a single line."""
    # For simple values, they're always single line
    if isinstance(assign_node.value, (ast.Constant, ast.Name, ast.Attribute)):
        return True

    # For complex expressions, check if they span multiple lines
    # We'll consider it multi-line if the end line is different from start line
    if hasattr(assign_node, "lineno") and assign_node.value is not None and hasattr(assign_node.value, "end_lineno"):
        return assign_node.lineno == assign_node.value.end_lineno

    return True


def collect_variable_usage_and_stores_with_nodes(
    function_node: ast.AST,
) -> tuple[dict[str, list[ast.Name]], set[str], dict[str, ast.Assign | ast.AnnAssign]]:
    variable_usage: typing.Final[defaultdict[str, list[ast.Name]]] = defaultdict(list)
    assigned_variable_names: typing.Final[set[str]] = set()
    variable_assignments: typing.Final[dict[str, ast.Assign | ast.AnnAssign]] = {}

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

            for one_target in assign_node.targets:
                one_names = list(extract_names(one_target))
                assigned_variable_names.update(one_names)
                # Store the assignment node for each variable
                for one_name in one_names:
                    variable_assignments[one_name] = assign_node
            self.generic_visit(assign_node)

        def visit_AugAssign(self, aug_assign_node: ast.AugAssign) -> None:
            assigned_variable_names.update(list(extract_names(aug_assign_node.target)))
            self.generic_visit(aug_assign_node)

        def visit_AnnAssign(self, ann_assign_node: ast.AnnAssign) -> None:
            extracted_names: typing.Final = list(extract_names(ann_assign_node.target))  # noqa: COP011
            assigned_variable_names.update(extracted_names)
            # Store the assignment node for each variable
            for one_name in extracted_names:
                variable_assignments[one_name] = ann_assign_node
            self.generic_visit(ann_assign_node)

    UsageCollector().visit(function_node)
    return dict(variable_usage), assigned_variable_names, variable_assignments


def is_used_in_next_line(assign_node: ast.Assign | ast.AnnAssign, usage_nodes: list[ast.Name]) -> bool:
    """Check if variable is used in the immediate next line."""
    if not usage_nodes:
        return False

    # Find the load usage (actual use of the variable)
    load_usages: typing.Final = [one_node for one_node in usage_nodes if isinstance(one_node.ctx, ast.Load)]
    if not load_usages:
        return False

    first_load: typing.Final = load_usages[0]

    # Check if the usage is on the line immediately following the assignment
    return first_load.lineno == assign_node.lineno + 1


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
        usage_and_stores: typing.Final = collect_variable_usage_and_stores_with_nodes(ast_node)
        variable_usages: typing.Final = usage_and_stores[0]
        assigned_variable_names: typing.Final = usage_and_stores[1]
        variable_assignments: typing.Final = usage_and_stores[2]

        for variable_name, usages in variable_usages.items():
            if variable_name.startswith("_") or variable_name in {"self", "cls"}:
                continue

            store_count = len(
                [one_usage_element for one_usage_element in usages if isinstance(one_usage_element.ctx, ast.Store)]
            )
            load_count = len(
                [one_usage_element for one_usage_element in usages if isinstance(one_usage_element.ctx, ast.Load)]
            )

            # Check if variable is assigned once and used once
            if store_count == 1 and load_count == 1 and variable_name in assigned_variable_names:
                # Get the assignment node
                assign_node = variable_assignments.get(variable_name)
                if not assign_node:
                    continue

                # Check if it's a single-line assignment
                if not is_single_line_assignment(assign_node):
                    continue

                # Check if it's used in the next line
                if is_used_in_next_line(assign_node, usages):
                    # Only flag the variable that is assigned and then immediately used
                    # Find the store usage (assignment)
                    store_usages = [one_node for one_node in usages if isinstance(one_node.ctx, ast.Store)]
                    if store_usages:
                        first_store = store_usages[0]
                        self.violations.append(
                            Violation(
                                line_number=first_store.lineno,
                                column_number=first_store.col_offset,
                                violation_code=ViolationCodes.TEMP_VAR,
                            )
                        )

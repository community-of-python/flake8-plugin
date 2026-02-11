from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def _is_ignored_target(target_node: ast.expr) -> bool:
    """Check if target should be ignored (e.g., underscore variables)."""
    # Ignore underscore variables
    return bool(isinstance(target_node, ast.Name) and target_node.id == "_")


@typing.final
class COP015ForLoopOnePrefixCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:
        self.violations: list[Violation] = []
        self.syntax_tree: typing.Final[ast.AST] = syntax_tree

    def visit_ListComp(self, ast_node: ast.ListComp) -> None:
        # Validate targets in generators (the 'v' in 'for v in lst')
        for one_comprehension in ast_node.generators:
            if not self._is_partial_unpacking(ast_node.elt, one_comprehension.target):
                self._validate_comprehension_target(one_comprehension.target, one_comprehension.iter)
        self.generic_visit(ast_node)

    def visit_SetComp(self, ast_node: ast.SetComp) -> None:
        # Validate targets in generators (the 'v' in 'for v in lst')
        for one_comprehension in ast_node.generators:
            if not self._is_partial_unpacking(ast_node.elt, one_comprehension.target):
                self._validate_comprehension_target(one_comprehension.target, one_comprehension.iter)
        self.generic_visit(ast_node)

    def visit_DictComp(self, ast_node: ast.DictComp) -> None:
        # Validate targets in generators (the 'v' in 'for v in lst')
        # For dict comprehensions, we consider both key and value
        # key and value are both used
        for one_comprehension in ast_node.generators:
            if not self._is_partial_unpacking_expr_count(2, one_comprehension.target):
                self._validate_comprehension_target(one_comprehension.target, one_comprehension.iter)
        self.generic_visit(ast_node)

    def visit_For(self, ast_node: ast.For) -> None:
        # Validate target variables in regular for-loops
        # Apply same unpacking logic as comprehensions
        # For-loops don't have an expression that references vars
        if not self._is_partial_unpacking_expr_count(1, ast_node.target):
            self._validate_comprehension_target(ast_node.target, ast_node.iter)
        self.generic_visit(ast_node)

    def visit_GeneratorExp(self, ast_node: ast.GeneratorExp) -> None:
        # Validate targets in generators (the 'v' in 'for v in lst')
        for one_comprehension in ast_node.generators:
            if not self._is_partial_unpacking(ast_node.elt, one_comprehension.target):
                self._validate_comprehension_target(one_comprehension.target, one_comprehension.iter)
        self.generic_visit(ast_node)

    def _is_partial_unpacking(self, expression: ast.expr, target_node: ast.expr) -> bool:
        """Check if this is partial unpacking (referencing fewer vars than unpacked)."""
        return self._is_partial_unpacking_expr_count(self._count_referenced_vars(expression), target_node)

    def _is_partial_unpacking_expr_count(self, expression_count: int, target_node: ast.expr) -> bool:
        """Check if this is partial unpacking given expression variable count."""
        target_count: typing.Final = self._count_unpacked_vars(target_node)
        return target_count > expression_count and target_count > 1

    def _is_literal_range(self, iter_node: ast.expr) -> bool:
        """Check if the iteration is over a literal range() call."""
        # Check for direct range() call
        if isinstance(iter_node, ast.Call) and isinstance(iter_node.func, ast.Name) and iter_node.func.id == "range":
            # Check if all arguments are literals (no variables)
            for one_arg in iter_node.args:
                if not isinstance(one_arg, (ast.Constant, ast.UnaryOp)):
                    # If any argument is not a literal, this is not a literal range
                    # Note: UnaryOp is included to handle negative numbers like -1
                    return False
                # For UnaryOp (like -1), check if operand is a literal
                if isinstance(one_arg, ast.UnaryOp) and not isinstance(one_arg.operand, ast.Constant):
                    return False
            return True
        return False

    def _count_referenced_vars(self, expression: ast.expr) -> int:
        """Count how many variables are referenced in the expression."""
        if isinstance(expression, ast.Name):
            return 1
        if isinstance(expression, ast.Tuple):
            return len([one_element for one_element in expression.elts if isinstance(one_element, ast.Name)])
        # For simplicity, assume other expressions reference 1 variable
        # This covers cases like function calls, attributes, etc.
        return 1

    def _count_unpacked_vars(self, target_node: ast.expr) -> int:
        """Count how many variables are unpacked in the target."""
        if isinstance(target_node, ast.Name):
            return 1
        if isinstance(target_node, ast.Tuple):
            return len([one_element for one_element in target_node.elts if isinstance(one_element, ast.Name)])
        return 0

    def _validate_comprehension_target(self, target_node: ast.expr, iter_node: ast.expr | None = None) -> None:
        """Validate that comprehension target follows the one_ prefix rule."""
        # Skip validation if iterating over literal range()
        if iter_node is not None and self._is_literal_range(iter_node):
            return

        # Skip ignored targets (underscore, unpacking)
        if _is_ignored_target(target_node):
            return

        # For simple names, validate the prefix
        if isinstance(target_node, ast.Name):
            if not self._has_valid_one_prefix(target_node.id):
                self.violations.append(
                    Violation(
                        line_number=target_node.lineno,
                        column_number=target_node.col_offset,
                        violation_code=ViolationCodes.FOR_LOOP_VARIABLE_PREFIX,
                    )
                )
        # For tuples (unpacking), validate each element
        elif isinstance(target_node, ast.Tuple):
            for one_element in target_node.elts:
                if isinstance(one_element, ast.Name) and not self._has_valid_one_prefix(one_element.id):
                    self.violations.append(
                        Violation(
                            line_number=one_element.lineno,
                            column_number=one_element.col_offset,
                            violation_code=ViolationCodes.FOR_LOOP_VARIABLE_PREFIX,
                        )
                    )

    def _has_valid_one_prefix(self, identifier: str) -> bool:
        """Check if identifier has valid one_ prefix."""
        # Allow underscore variables
        if identifier == "_":
            return True

        # Check for one_ prefix
        return identifier.startswith("one_")

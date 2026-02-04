from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import FINAL_CLASS_EXCLUDED_BASES, MIN_NAME_LENGTH
from community_of_python_flake8_plugin.utils import find_parent_class_definition
from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def check_is_ignored_name(identifier: str) -> bool:
    if identifier == "_":
        return True
    if identifier.isupper():
        return True
    if identifier in {"value", "values", "pattern"}:
        return True
    if identifier.startswith("__") and identifier.endswith("__"):
        return True
    return bool(identifier.startswith("_"))


def check_is_whitelisted_annotation(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    if isinstance(annotation, ast.Name):
        return annotation.id in {"fixture", "Faker"}
    if isinstance(annotation, ast.Attribute) and isinstance(annotation.value, ast.Name):
        return annotation.value.id in {"pytest", "faker"}
    return False


def check_is_pytest_fixture(ast_node: ast.AST) -> bool:
    if not isinstance(ast_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    return any(check_is_fixture_decorator(decorator) for decorator in ast_node.decorator_list)  # noqa: COP011


def check_is_fixture_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name):
        return decorator.id == "fixture"
    if isinstance(decorator, ast.Attribute):
        return decorator.attr == "fixture" and isinstance(decorator.value, ast.Name) and decorator.value.id == "pytest"
    return False


def check_inherits_from_whitelisted_class(class_node: ast.ClassDef) -> bool:
    for base_class in class_node.bases:
        if isinstance(base_class, ast.Name) and base_class.id in FINAL_CLASS_EXCLUDED_BASES:
            return True
        if isinstance(base_class, ast.Attribute) and base_class.attr in FINAL_CLASS_EXCLUDED_BASES:
            return True
    return False


@typing.final
class COP004NameLengthCheck(ast.NodeVisitor):
    def __init__(self, tree: ast.AST) -> None:  # noqa: COP006
        self.violations: list[Violation] = []
        self.syntax_tree: typing.Final[ast.AST] = tree

    def visit_AnnAssign(self, ast_node: ast.AnnAssign) -> None:
        if isinstance(ast_node.target, ast.Name):
            parent_class: typing.Final = find_parent_class_definition(self.syntax_tree, ast_node)  # noqa: COP011
            self.validate_name_length(ast_node.target.id, ast_node, parent_class)
        self.generic_visit(ast_node)

    def visit_Assign(self, ast_node: ast.Assign) -> None:
        for target in ast_node.targets:
            if isinstance(target, ast.Name):
                parent_class = find_parent_class_definition(self.syntax_tree, ast_node)  # noqa: COP011
                self.validate_name_length(target.id, ast_node, parent_class)
        self.generic_visit(ast_node)

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        parent_class: typing.Final = find_parent_class_definition(self.syntax_tree, ast_node)  # noqa: COP011
        self.validate_function_name(ast_node, parent_class)
        self.validate_function_args(ast_node)
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        parent_class: typing.Final = find_parent_class_definition(self.syntax_tree, ast_node)  # noqa: COP011
        self.validate_function_name(ast_node, parent_class)
        self.validate_function_args(ast_node)
        self.generic_visit(ast_node)

    def visit_ClassDef(self, ast_node: ast.ClassDef) -> None:
        if not ast_node.name.startswith("Test"):
            self.validate_class_name_length(ast_node)
        self.generic_visit(ast_node)

    def validate_name_length(self, identifier: str, ast_node: ast.stmt, parent_class: ast.ClassDef | None) -> None:
        if check_is_ignored_name(identifier):
            return

        # Only apply parent class exemption for assignments within classes
        if (
            parent_class
            and isinstance(ast_node, (ast.AnnAssign, ast.Assign))
            and check_inherits_from_whitelisted_class(parent_class)
        ):
            return

        if len(identifier) < MIN_NAME_LENGTH:
            # Determine the appropriate violation code based on context
            if isinstance(ast_node, ast.AnnAssign):
                name_violation_code = ViolationCodes.ATTRIBUTE_NAME_LENGTH
            elif isinstance(ast_node, ast.Assign):
                name_violation_code = ViolationCodes.VARIABLE_NAME_LENGTH
            else:
                # This shouldn't happen with current AST node types, but fall back to generic if needed
                name_violation_code = ViolationCodes.ATTRIBUTE_NAME_LENGTH

            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=name_violation_code,
                )
            )

    def validate_function_name(
        self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef, parent_class: ast.ClassDef | None
    ) -> None:
        if ast_node.name == "main":
            return
        if check_is_ignored_name(ast_node.name):
            return
        if parent_class and check_inherits_from_whitelisted_class(parent_class):
            return
        if check_is_pytest_fixture(ast_node):
            return

        if len(ast_node.name) < MIN_NAME_LENGTH:
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCodes.FUNCTION_NAME_LENGTH,
                )
            )

    def validate_function_args(self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        # Process all argument types
        for argument in ast_node.args.posonlyargs:
            self.validate_argument_name_length(argument)
        for argument in ast_node.args.args:
            self.validate_argument_name_length(argument)
        for argument in ast_node.args.kwonlyargs:
            self.validate_argument_name_length(argument)

        if ast_node.args.vararg is not None:
            self.validate_argument_name_length(ast_node.args.vararg)
        if ast_node.args.kwarg is not None:
            self.validate_argument_name_length(ast_node.args.kwarg)

    def validate_argument_name_length(self, argument: ast.arg) -> None:
        if argument.arg in {"self", "cls"}:
            return
        if check_is_ignored_name(argument.arg):
            return
        if check_is_whitelisted_annotation(argument.annotation):
            return

        if len(argument.arg) < MIN_NAME_LENGTH:
            self.violations.append(
                Violation(
                    line_number=argument.lineno,
                    column_number=argument.col_offset,
                    violation_code=ViolationCodes.ARGUMENT_NAME_LENGTH,
                )
            )

    def validate_class_name_length(self, ast_node: ast.ClassDef) -> None:
        if check_is_ignored_name(ast_node.name):
            return

        if len(ast_node.name) < MIN_NAME_LENGTH:
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=ViolationCodes.CLASS_NAME_LENGTH,
                )
            )

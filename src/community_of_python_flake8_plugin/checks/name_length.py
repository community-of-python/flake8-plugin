from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import FINAL_CLASS_EXCLUDED_BASES, MIN_NAME_LENGTH
from community_of_python_flake8_plugin.utils import check_inherits_from_bases, find_parent_class_definition
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


@typing.final
class COP004NameLengthCheck(ast.NodeVisitor):
    def __init__(self, tree: ast.AST) -> None:  # noqa: COP006
        self.violations: list[Violation] = []
        self.syntax_tree: typing.Final[ast.AST] = tree

    def visit_AnnAssign(self, ast_node: ast.AnnAssign) -> None:
        if isinstance(ast_node.target, ast.Name):
            self.validate_name_length(
                ast_node.target.id, ast_node, find_parent_class_definition(self.syntax_tree, ast_node)
            )
        self.generic_visit(ast_node)

    def visit_Assign(self, ast_node: ast.Assign) -> None:
        for target in ast_node.targets:
            if isinstance(target, ast.Name):
                self.validate_name_length(target.id, ast_node, find_parent_class_definition(self.syntax_tree, ast_node))
        self.generic_visit(ast_node)

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        self.validate_function_name(ast_node, find_parent_class_definition(self.syntax_tree, ast_node))
        self.validate_function_args(ast_node)
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        self.validate_function_name(ast_node, find_parent_class_definition(self.syntax_tree, ast_node))
        self.validate_function_args(ast_node)
        self.generic_visit(ast_node)

    def visit_ClassDef(self, ast_node: ast.ClassDef) -> None:
        if not ast_node.name.startswith("Test"):
            self.validate_class_name_length(ast_node)
        self.generic_visit(ast_node)

    def visit_ListComp(self, ast_node: ast.ListComp) -> None:
        for comprehension in ast_node.generators:
            self._validate_comprehension_target(comprehension.target)
        self.generic_visit(ast_node)

    def visit_SetComp(self, ast_node: ast.SetComp) -> None:
        for comprehension in ast_node.generators:
            self._validate_comprehension_target(comprehension.target)
        self.generic_visit(ast_node)

    def visit_DictComp(self, ast_node: ast.DictComp) -> None:
        for comprehension in ast_node.generators:
            self._validate_comprehension_target(comprehension.target)
        self.generic_visit(ast_node)

    def visit_Lambda(self, ast_node: ast.Lambda) -> None:
        self._validate_function_args(ast_node.args)
        self.generic_visit(ast_node)

    def visit_With(self, ast_node: ast.With) -> None:
        for item in ast_node.items:
            if item.optional_vars is not None:
                self._validate_with_target(item.optional_vars)
        self.generic_visit(ast_node)

    def visit_ExceptHandler(self, ast_node: ast.ExceptHandler) -> None:
        if ast_node.name is not None:
            self._validate_except_target(ast_node)
        self.generic_visit(ast_node)

    def visit_GeneratorExp(self, ast_node: ast.GeneratorExp) -> None:
        for comprehension in ast_node.generators:
            self._validate_comprehension_target(comprehension.target)
        self.generic_visit(ast_node)

    def _validate_function_args(self, arguments_node: ast.arguments) -> None:
        # Process all argument types
        for argument in arguments_node.posonlyargs:
            self._validate_argument_name_length(argument)
        for argument in arguments_node.args:
            self._validate_argument_name_length(argument)
        for argument in arguments_node.kwonlyargs:
            self._validate_argument_name_length(argument)

        if arguments_node.vararg is not None:
            self._validate_argument_name_length(arguments_node.vararg)
        if arguments_node.kwarg is not None:
            self._validate_argument_name_length(arguments_node.kwarg)

    def _validate_argument_name_length(self, argument: ast.arg) -> None:
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

    def _validate_comprehension_target(self, comprehension_target: ast.expr) -> None:
        if isinstance(comprehension_target, ast.Name):
            # For comprehension targets, we'll treat them as variables
            if not check_is_ignored_name(comprehension_target.id) and len(comprehension_target.id) < MIN_NAME_LENGTH:
                self.violations.append(
                    Violation(
                        line_number=comprehension_target.lineno,
                        column_number=comprehension_target.col_offset,
                        violation_code=ViolationCodes.VARIABLE_NAME_LENGTH,
                    )
                )
        elif isinstance(comprehension_target, ast.Tuple):
            # Handle tuple unpacking in comprehensions like [(a, b) for a, b in pairs]
            for elt in comprehension_target.elts:
                self._validate_comprehension_target(elt)

    def _validate_with_target(self, target_node: ast.expr) -> None:
        if isinstance(target_node, ast.Name):
            # For with targets, we'll treat them as variables
            if not check_is_ignored_name(target_node.id) and len(target_node.id) < MIN_NAME_LENGTH:
                self.violations.append(
                    Violation(
                        line_number=target_node.lineno,
                        column_number=target_node.col_offset,
                        violation_code=ViolationCodes.VARIABLE_NAME_LENGTH,
                    )
                )
        elif isinstance(target_node, ast.Tuple):
            # Handle tuple unpacking in with statements like with open(f1) as f1, open(f2) as f2:
            for elt in target_node.elts:
                self._validate_with_target(elt)

    def _validate_except_target(self, ast_node: ast.ExceptHandler) -> None:
        # For except targets, we'll treat them as variables
        if (
            ast_node.name is not None
            and not check_is_ignored_name(ast_node.name)
            and len(ast_node.name) < MIN_NAME_LENGTH
        ):
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=0,  # ast.ExceptHandler doesn't have col_offset
                    violation_code=ViolationCodes.VARIABLE_NAME_LENGTH,
                )
            )

    def validate_name_length(self, identifier: str, ast_node: ast.stmt, parent_class: ast.ClassDef | None) -> None:
        if check_is_ignored_name(identifier):
            return

        # Only apply parent class exemption for assignments within classes
        if (
            parent_class
            and isinstance(ast_node, (ast.AnnAssign, ast.Assign))
            and check_inherits_from_bases(parent_class, FINAL_CLASS_EXCLUDED_BASES)
        ):
            return

        if len(identifier) < MIN_NAME_LENGTH:
            # Determine if this is an attribute (inside a class) or variable (at module level)
            self.violations.append(
                Violation(
                    line_number=ast_node.lineno,
                    column_number=ast_node.col_offset,
                    violation_code=(
                        ViolationCodes.ATTRIBUTE_NAME_LENGTH
                        if parent_class is not None
                        else ViolationCodes.VARIABLE_NAME_LENGTH
                    ),
                )
            )

    def validate_function_name(
        self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef, parent_class: ast.ClassDef | None
    ) -> None:
        if ast_node.name == "main":
            return
        if check_is_ignored_name(ast_node.name):
            return
        if parent_class and check_inherits_from_bases(parent_class, FINAL_CLASS_EXCLUDED_BASES):
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

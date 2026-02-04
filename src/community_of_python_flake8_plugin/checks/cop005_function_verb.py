from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import FINAL_CLASS_EXCLUDED_BASES, VERB_PREFIXES
from community_of_python_flake8_plugin.utils import find_parent_class_definition
from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
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


def check_is_verb_name(identifier: str) -> bool:
    return any(identifier == verb or identifier.startswith(f"{verb}_") for verb in VERB_PREFIXES)


def check_is_property(function_node: ast.AST) -> bool:
    if not isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    return any(check_is_property_decorator(decorator) for decorator in function_node.decorator_list)  # noqa: COP007


def check_is_property_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name):
        return decorator.id == "property"
    if isinstance(decorator, ast.Attribute) and decorator.attr in {"property", "setter", "cached_property"}:
        if isinstance(decorator.value, ast.Name) and decorator.value.id == "functools":
            return decorator.attr == "cached_property"
        return decorator.attr in {"property", "setter"}
    return False


def check_is_pytest_fixture(function_node: ast.AST) -> bool:
    if not isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    return any(check_is_fixture_decorator(decorator) for decorator in function_node.decorator_list)  # noqa: COP007


def check_is_fixture_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name):
        return decorator.id == "fixture"
    if isinstance(decorator, ast.Attribute):
        return decorator.attr == "fixture" and isinstance(decorator.value, ast.Name) and decorator.value.id == "pytest"
    return False


def retrieve_parent_class(syntax_tree: ast.AST, ast_node: ast.AST) -> ast.ClassDef | None:
    return find_parent_class_definition(syntax_tree, ast_node)


@typing.final
class COP005FunctionVerbCheck(ast.NodeVisitor):
    def __init__(self, tree: ast.AST) -> None:  # noqa: COP004G
        self.violations: list[Violation] = []
        self.syntax_tree: typing.Final[ast.AST] = tree

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        parent_class: typing.Final = retrieve_parent_class(self.syntax_tree, ast_node)  # noqa: COP007
        self.validate_function_name(ast_node, parent_class)
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        parent_class: typing.Final = retrieve_parent_class(self.syntax_tree, ast_node)  # noqa: COP007
        self.validate_function_name(ast_node, parent_class)
        self.generic_visit(ast_node)

    def validate_function_name(
        self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef, parent_class: ast.ClassDef | None
    ) -> None:
        if (
            ast_node.name == "main"
            or (ast_node.name.startswith("__") and ast_node.name.endswith("__"))
            or check_is_ignored_name(ast_node.name)
            or (parent_class and self.check_inherits_from_whitelisted_class(parent_class))
            or check_is_property(ast_node)
            or check_is_pytest_fixture(ast_node)
            or check_is_verb_name(ast_node.name)
        ):
            return

        if len(ast_node.name) < 3:  # Short names are likely acronyms or special cases
            return

        self.violations.append(
            Violation(
                line_number=ast_node.lineno,
                column_number=ast_node.col_offset,
                violation_code=ViolationCode.FUNCTION_VERB,
            )
        )

    def check_inherits_from_whitelisted_class(self, ast_node: ast.ClassDef) -> bool:
        for base_class in ast_node.bases:
            if isinstance(base_class, ast.Name) and base_class.id in FINAL_CLASS_EXCLUDED_BASES:
                return True
            if isinstance(base_class, ast.Attribute) and base_class.attr in FINAL_CLASS_EXCLUDED_BASES:
                return True
        return False

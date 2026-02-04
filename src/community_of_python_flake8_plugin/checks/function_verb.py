from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import FINAL_CLASS_EXCLUDED_BASES, VERB_PREFIXES
from community_of_python_flake8_plugin.utils import check_inherits_from_bases, find_parent_class_definition
from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def check_is_ignored_name(identifier: str) -> bool:
    if identifier == "main":
        return True
    if identifier.startswith("__") and identifier.endswith("__"):
        return True
    return bool(identifier.startswith("_"))


def check_is_verb_name(identifier: str) -> bool:
    return any(identifier == verb or identifier.startswith(f"{verb}_") for verb in VERB_PREFIXES)


def check_is_property(function_node: ast.AST) -> bool:
    if not isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    return any(check_is_property_decorator(decorator) for decorator in function_node.decorator_list)  # noqa: COP011


def check_is_property_decorator(decorator: ast.expr) -> bool:  # noqa: PLR0911
    if isinstance(decorator, ast.Name):
        return decorator.id in {"property", "cached_property"}

    # Handle attribute references like @functools.cached_property
    if isinstance(decorator, ast.Attribute) and decorator.attr in {"property", "setter", "cached_property"}:
        if isinstance(decorator.value, ast.Name) and decorator.value.id == "functools":
            return decorator.attr == "cached_property"
        return decorator.attr in {"property", "setter"}

    # Handle decorator calls like @property() or @functools.cached_property()
    if isinstance(decorator, ast.Call):
        if isinstance(decorator.func, ast.Name):
            return decorator.func.id in {"property", "cached_property"}
        if isinstance(decorator.func, ast.Attribute):
            if (
                decorator.func.attr in {"property", "setter", "cached_property"}
                and isinstance(decorator.func.value, ast.Name)
                and decorator.func.value.id == "functools"
            ):
                return decorator.func.attr == "cached_property"
            if decorator.func.attr in {"property", "setter", "cached_property"}:
                return decorator.func.attr in {"property", "setter"}

    return False


def check_is_pytest_fixture(function_node: ast.AST) -> bool:
    if not isinstance(function_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    return any(check_is_fixture_decorator(decorator) for decorator in function_node.decorator_list)  # noqa: COP011


def check_is_fixture_decorator(decorator: ast.expr) -> bool:
    if isinstance(decorator, ast.Name):
        return decorator.id == "fixture"
    if isinstance(decorator, ast.Attribute):
        return decorator.attr == "fixture" and isinstance(decorator.value, ast.Name) and decorator.value.id == "pytest"
    # Handle cases where decorator might be a call like @pytest.fixture(name="events")
    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
        return (
            decorator.func.attr == "fixture"
            and isinstance(decorator.func.value, ast.Name)
            and decorator.func.value.id == "pytest"
        )
    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
        return decorator.func.id == "fixture"
    return False


@typing.final
class FunctionVerbCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:
        self.violations: list[Violation] = []
        self.syntax_tree: typing.Final[ast.AST] = syntax_tree

    def visit_FunctionDef(self, ast_node: ast.FunctionDef) -> None:
        self.validate_function_name(ast_node, find_parent_class_definition(self.syntax_tree, ast_node))
        self.generic_visit(ast_node)

    def visit_AsyncFunctionDef(self, ast_node: ast.AsyncFunctionDef) -> None:
        self.validate_function_name(ast_node, find_parent_class_definition(self.syntax_tree, ast_node))
        self.generic_visit(ast_node)

    def validate_function_name(
        self, ast_node: ast.FunctionDef | ast.AsyncFunctionDef, parent_class: ast.ClassDef | None
    ) -> None:
        if (
            check_is_ignored_name(ast_node.name)
            or (parent_class and check_inherits_from_bases(parent_class, FINAL_CLASS_EXCLUDED_BASES))
            or check_is_property(ast_node)
            or check_is_pytest_fixture(ast_node)
            or check_is_verb_name(ast_node.name)
        ):
            return

        self.violations.append(
            Violation(
                line_number=ast_node.lineno,
                column_number=ast_node.col_offset,
                violation_code=ViolationCodes.FUNCTION_VERB,
            )
        )

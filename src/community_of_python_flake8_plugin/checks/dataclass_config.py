from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import FINAL_CLASS_EXCLUDED_BASES
from community_of_python_flake8_plugin.utils import check_inherits_from_bases
from community_of_python_flake8_plugin.violation_codes import ViolationCodes
from community_of_python_flake8_plugin.violations import Violation


def is_dataclass_decorator(decorator: ast.expr) -> bool:
    """Check if the decorator is a dataclass decorator."""
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    if isinstance(decorator, ast.Name):
        return decorator.id == "dataclass"
    if isinstance(decorator, ast.Attribute):
        return decorator.attr == "dataclass"
    return False


def has_required_dataclass_params(decorator: ast.expr) -> bool:
    """Check if dataclass decorator has the required parameters."""
    if not isinstance(decorator, ast.Call):
        return False

    keywords: typing.Final = {
        one_keyword_item.arg: one_keyword_item.value
        for one_keyword_item in decorator.keywords
        if isinstance(one_keyword_item.value, ast.Constant)
    }
    kw_only_param: typing.Final = keywords.get("kw_only")
    slots_param: typing.Final = keywords.get("slots")
    frozen_param: typing.Final = keywords.get("frozen")
    return (
        kw_only_param is not None
        and isinstance(kw_only_param, ast.Constant)
        and kw_only_param.value is True
        and slots_param is not None
        and isinstance(slots_param, ast.Constant)
        and slots_param.value is True
        and frozen_param is not None
        and isinstance(frozen_param, ast.Constant)
        and frozen_param.value is True
    )


def is_pydantic_model(class_node: ast.ClassDef) -> bool:
    """Check if class inherits from Pydantic BaseModel or RootModel."""
    for one_base_class in class_node.bases:
        if isinstance(one_base_class, ast.Name) and one_base_class.id in {"BaseModel", "RootModel"}:
            return True
        if isinstance(one_base_class, ast.Attribute) and one_base_class.attr in {"BaseModel", "RootModel"}:
            return True
    return False


def is_model_factory(class_node: ast.ClassDef) -> bool:
    """Check if class inherits from ModelFactory."""
    for one_base_class in class_node.bases:
        if isinstance(one_base_class, ast.Name) and one_base_class.id in {"ModelFactory", "SQLAlchemyFactory"}:
            return True
        if isinstance(one_base_class, ast.Attribute) and one_base_class.attr in {"ModelFactory", "SQLAlchemyFactory"}:
            return True
    return False


@typing.final
class DataclassConfigCheck(ast.NodeVisitor):
    def __init__(self, syntax_tree: ast.AST) -> None:  # noqa: ARG002
        self.violations: list[Violation] = []

    def visit_ClassDef(self, ast_node: ast.ClassDef) -> None:
        # Skip whitelisted classes and classes that inherit from Exception or other special classes
        if (
            check_inherits_from_bases(ast_node, FINAL_CLASS_EXCLUDED_BASES)
            or is_pydantic_model(ast_node)
            or is_model_factory(ast_node)
            or self._inherits_from_exception(ast_node)
        ):
            self.generic_visit(ast_node)
            return

        # Check for dataclass decorator
        for one_decorator in ast_node.decorator_list:
            if is_dataclass_decorator(one_decorator):
                if not has_required_dataclass_params(one_decorator):
                    self.violations.append(
                        Violation(
                            line_number=ast_node.lineno,
                            column_number=ast_node.col_offset,
                            violation_code=ViolationCodes.DATACLASS_CONFIG,
                        )
                    )
                break

        self.generic_visit(ast_node)

    def _inherits_from_exception(self, ast_node: ast.ClassDef) -> bool:
        """Check if class inherits from Exception or its subclasses."""
        for one_base in ast_node.bases:
            if isinstance(one_base, ast.Name) and ("Error" in one_base.id or "Exception" in one_base.id):
                return True
            if isinstance(one_base, ast.Attribute) and ("Error" in one_base.attr or "Exception" in one_base.attr):
                return True
        return False

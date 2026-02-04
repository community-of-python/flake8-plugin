from __future__ import annotations
import ast
import typing

from community_of_python_flake8_plugin.constants import FINAL_CLASS_EXCLUDED_BASES
from community_of_python_flake8_plugin.violation_codes import ViolationCodes as ViolationCode
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

    # Check if all required parameters are present
    kw_only_present = slots_present = frozen_present = False
    for keyword in decorator.keywords:
        if keyword.arg == "kw_only" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
            kw_only_present = True
        elif keyword.arg == "slots" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
            slots_present = True
        elif keyword.arg == "frozen" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
            frozen_present = True

    return kw_only_present and slots_present and frozen_present


def is_inherited_from_whitelisted_class(class_node: ast.ClassDef) -> bool:
    """Check if class inherits from whitelisted base classes."""
    for base_class in class_node.bases:
        if isinstance(base_class, ast.Name) and base_class.id in FINAL_CLASS_EXCLUDED_BASES:
            return True
        if isinstance(base_class, ast.Attribute) and base_class.attr in FINAL_CLASS_EXCLUDED_BASES:
            return True
    return False


def is_pydantic_model(class_node: ast.ClassDef) -> bool:
    """Check if class inherits from Pydantic BaseModel or RootModel."""
    for base_class in class_node.bases:
        if isinstance(base_class, ast.Name) and base_class.id in {"BaseModel", "RootModel"}:
            return True
        if isinstance(base_class, ast.Attribute) and base_class.attr in {"BaseModel", "RootModel"}:
            return True
    return False


def is_model_factory(class_node: ast.ClassDef) -> bool:
    """Check if class inherits from ModelFactory."""
    for base_class in class_node.bases:
        if isinstance(base_class, ast.Name) and base_class.id == "ModelFactory":
            return True
        if isinstance(base_class, ast.Attribute) and base_class.attr == "ModelFactory":
            return True
    return False


@typing.final
class COP010DataclassConfigCheck(ast.NodeVisitor):
    def __init__(self, tree: ast.AST) -> None:
        self.violations: list[Violation] = []

    def visit_ClassDef(self, ast_node: ast.ClassDef) -> None:
        # Skip whitelisted classes and classes that inherit from Exception or other special classes
        if (
            is_inherited_from_whitelisted_class(ast_node)
            or is_pydantic_model(ast_node)
            or is_model_factory(ast_node)
            or self._inherits_from_exception(ast_node)
        ):
            self.generic_visit(ast_node)
            return

        # Check for dataclass decorator
        for decorator in ast_node.decorator_list:
            if is_dataclass_decorator(decorator):
                if not has_required_dataclass_params(decorator):
                    self.violations.append(
                        Violation(
                            line_number=ast_node.lineno,
                            column_number=ast_node.col_offset,
                            violation_code=ViolationCode.DATACLASS_CONFIG,
                        )
                    )
                break

        self.generic_visit(ast_node)

    def _inherits_from_exception(self, ast_node: ast.ClassDef) -> bool:
        """Check if class inherits from Exception or its subclasses."""
        for base in ast_node.bases:
            if isinstance(base, ast.Name):
                # Check if base class name contains "Error" or "Exception"
                if "Error" in base.id or "Exception" in base.id:
                    return True
            elif isinstance(base, ast.Attribute):
                # Check if base class name contains "Error" or "Exception"
                if "Error" in base.attr or "Exception" in base.attr:
                    return True
        return len(ast_node.bases) > 0  # Skip all classes that inherit from anything

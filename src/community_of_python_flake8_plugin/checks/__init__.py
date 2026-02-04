from __future__ import annotations
import ast
import typing

# TODO: do auto discovery from checks directory
from community_of_python_flake8_plugin.checks.cop001_module_import import COP001ModuleImportCheck
from community_of_python_flake8_plugin.checks.cop002_stdlib_import import COP002StdlibImportCheck
from community_of_python_flake8_plugin.checks.cop003_scalar_annotation import COP003ScalarAnnotationCheck
from community_of_python_flake8_plugin.checks.cop004_name_length import COP004NameLengthCheck
from community_of_python_flake8_plugin.checks.cop005_function_verb import COP005FunctionVerbCheck
from community_of_python_flake8_plugin.checks.cop006_async_get_prefix import COP006AsyncGetPrefixCheck
from community_of_python_flake8_plugin.checks.cop007_temp_var import COP007TempVarCheck
from community_of_python_flake8_plugin.checks.cop008_final_class import COP008FinalClassCheck
from community_of_python_flake8_plugin.checks.cop009_mapping_proxy import COP009MappingProxyCheck
from community_of_python_flake8_plugin.checks.cop010_dataclass_config import COP010DataclassConfigCheck
from community_of_python_flake8_plugin.utils import check_module_has_all_declaration


if typing.TYPE_CHECKING:
    from community_of_python_flake8_plugin.violations import Violation


# TODO: do for-loop here
def execute_all_validations(syntax_tree: ast.AST) -> list[Violation]:
    contains_all_declaration: typing.Final = (
        check_module_has_all_declaration(syntax_tree) if isinstance(syntax_tree, ast.Module) else False
    )
    collected_violations: typing.Final[list[Violation]] = []

    # COP001: Use module import when importing more than two names
    cop001_validator: typing.Final = COP001ModuleImportCheck(contains_all_declaration)
    cop001_validator.visit(syntax_tree)
    collected_violations.extend(cop001_validator.violations)

    # COP002: Import standard library modules as whole modules
    cop002_validator: typing.Final = COP002StdlibImportCheck()
    cop002_validator.visit(syntax_tree)
    collected_violations.extend(cop002_validator.violations)

    # COP003: Avoid explicit scalar type annotations
    cop003_validator: typing.Final = COP003ScalarAnnotationCheck(syntax_tree)
    cop003_validator.visit(syntax_tree)
    collected_violations.extend(cop003_validator.violations)

    # COP004: Name must be at least 8 characters
    cop004_validator: typing.Final = COP004NameLengthCheck(syntax_tree)
    cop004_validator.visit(syntax_tree)
    collected_violations.extend(cop004_validator.violations)

    # COP005: Function identifier must be a verb
    cop005_validator: typing.Final = COP005FunctionVerbCheck(syntax_tree)
    cop005_validator.visit(syntax_tree)
    collected_violations.extend(cop005_validator.violations)

    # COP006: Avoid get_ prefix in async function names
    cop006_validator: typing.Final = COP006AsyncGetPrefixCheck()
    cop006_validator.visit(syntax_tree)
    collected_violations.extend(cop006_validator.violations)

    # COP007: Avoid temporary variables used only once
    cop007_validator: typing.Final = COP007TempVarCheck()
    cop007_validator.visit(syntax_tree)
    collected_violations.extend(cop007_validator.violations)

    # COP008: Classes should be marked typing.final
    cop008_validator: typing.Final = COP008FinalClassCheck()
    cop008_validator.visit(syntax_tree)
    collected_violations.extend(cop008_validator.violations)

    # COP009: Wrap module dictionaries with types.MappingProxyType
    cop009_validator: typing.Final = COP009MappingProxyCheck()
    cop009_validator.visit(syntax_tree)
    collected_violations.extend(cop009_validator.violations)

    # COP010: Use dataclasses with kw_only=True, slots=True, frozen=True
    cop010_validator: typing.Final = COP010DataclassConfigCheck()
    cop010_validator.visit(syntax_tree)
    collected_violations.extend(cop010_validator.violations)

    return collected_violations

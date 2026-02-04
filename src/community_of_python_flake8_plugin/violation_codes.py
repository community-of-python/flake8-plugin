from __future__ import annotations
import dataclasses
import typing


@typing.final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ViolationCodeItem:
    code: str  # noqa: COP004C
    description: str


@typing.final
class ViolationCodes:
    # Import related violations
    MODULE_IMPORT_MANY_NAMES = ViolationCodeItem(
        code="COP001", description="Use module import when importing more than two names"
    )
    STDLIB_IMPORT = ViolationCodeItem(code="COP002", description="Import stdlib modules as whole modules")

    # Type annotation violations
    SCALAR_ANNOTATION = ViolationCodeItem(
        code="COP003", description="Avoid explicit scalar type annotations with literal values"
    )

    # Naming violations (more specific codes)
    ATTRIBUTE_NAME_LENGTH = ViolationCodeItem(
        code="COP004A", description="Attribute name must be at least 8 characters"
    )
    VARIABLE_NAME_LENGTH = ViolationCodeItem(code="COP004V", description="Variable name must be at least 8 characters")
    ARGUMENT_NAME_LENGTH = ViolationCodeItem(code="COP004G", description="Argument name must be at least 8 characters")
    FUNCTION_NAME_LENGTH = ViolationCodeItem(code="COP004F", description="Function name must be at least 8 characters")
    CLASS_NAME_LENGTH = ViolationCodeItem(code="COP004C", description="Class name must be at least 8 characters")

    # Function related violations
    FUNCTION_VERB = ViolationCodeItem(code="COP005", description="Function name must start with a verb")
    ASYNC_GET_PREFIX = ViolationCodeItem(code="COP006", description="Avoid get_ prefix in async function names")

    # Variable usage violations
    TEMPORARY_VARIABLE = ViolationCodeItem(code="COP007", description="Inline variables that are used only once")

    # Class related violations
    FINAL_CLASS = ViolationCodeItem(code="COP008", description="Classes must be marked final with @typing.final")

    # Module level violations
    MAPPING_PROXY = ViolationCodeItem(code="COP009", description="Wrap module dictionaries with types.MappingProxyType")

    # Dataclass violations
    DATACLASS_CONFIG = ViolationCodeItem(
        code="COP010", description="Use dataclasses with kw_only=True, slots=True, frozen=True"
    )

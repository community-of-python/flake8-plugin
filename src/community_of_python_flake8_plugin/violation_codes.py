from __future__ import annotations
import dataclasses
import typing


@typing.final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ViolationCode:
    code: str  # noqa: COP004C
    description: str


@typing.final
class ViolationCodes:
    # Import related violations
    MODULE_IMPORT = ViolationCode(code="COP001", description="Use module import when importing more than two names")
    STDLIB_IMPORT = ViolationCode(code="COP002", description="Import standard library modules as whole modules")

    # Type annotation violations
    SCALAR_ANNOTATION = ViolationCode(code="COP003", description="Avoid explicit scalar type annotations")

    # Naming violations (more specific codes)
    ATTRIBUTE_NAME_LENGTH = ViolationCode(code="COP004A", description="Attribute name must be at least 8 characters")
    VARIABLE_NAME_LENGTH = ViolationCode(code="COP004V", description="Variable name must be at least 8 characters")
    ARGUMENT_NAME_LENGTH = ViolationCode(code="COP004G", description="Argument name must be at least 8 characters")
    FUNCTION_NAME_LENGTH = ViolationCode(code="COP004F", description="Function name must be at least 8 characters")
    CLASS_NAME_LENGTH = ViolationCode(code="COP004C", description="Class name must be at least 8 characters")

    # Function related violations
    FUNCTION_VERB = ViolationCode(code="COP005", description="Function identifier must be a verb")
    ASYNC_GET_PREFIX = ViolationCode(code="COP006", description="Avoid get_ prefix in async function names")

    # Variable usage violations
    TEMPORARY_VARIABLE = ViolationCode(code="COP007", description="Avoid temporary variables used only once")

    # Class related violations
    FINAL_CLASS = ViolationCode(code="COP008", description="Classes should be marked typing.final")

    # Module level violations
    MAPPING_PROXY = ViolationCode(code="COP009", description="Wrap module dictionaries with types.MappingProxyType")

    # Dataclass violations
    DATACLASS_CONFIG = ViolationCode(
        code="COP010", description="Use dataclasses with kw_only=True, slots=True, frozen=True"
    )

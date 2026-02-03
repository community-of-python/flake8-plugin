from __future__ import annotations
import dataclasses
import typing


@typing.final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class ViolationCode:
    code: str  # noqa: COP004
    description: str


@typing.final
class ViolationCodes:
    MODULE_IMPORT = ViolationCode(code="COP001", description="Use module import when importing more than two names")
    STDLIB_IMPORT = ViolationCode(code="COP002", description="Import standard library modules as whole modules")
    SCALAR_ANNOTATION = ViolationCode(code="COP003", description="Avoid explicit scalar type annotations")
    NAME_LENGTH = ViolationCode(code="COP004", description="Name must be at least 8 characters")
    FUNCTION_VERB = ViolationCode(code="COP005", description="Function identifier must be a verb")
    ASYNC_GET_PREFIX = ViolationCode(code="COP006", description="Avoid get_ prefix in async function names")
    TEMPORARY_VARIABLE = ViolationCode(code="COP007", description="Avoid temporary variables used only once")
    FINAL_CLASS = ViolationCode(code="COP008", description="Classes should be marked typing.final")
    MAPPING_PROXY = ViolationCode(code="COP009", description="Wrap module dictionaries with types.MappingProxyType")
    DATACLASS_CONFIG = ViolationCode(
        code="COP010", description="Use dataclasses with kw_only=True, slots=True, frozen=True"
    )

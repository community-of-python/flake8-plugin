from __future__ import annotations
import dataclasses
import typing


if typing.TYPE_CHECKING:
    from .violation_codes import ViolationCode


@typing.final
@dataclasses.dataclass(frozen=True)
class Violation:
    line_number: int
    column_number: int
    violation_code: ViolationCode

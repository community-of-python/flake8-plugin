from __future__ import annotations
import dataclasses
import typing


if typing.TYPE_CHECKING:
    from .violation_codes import ViolationCodeItem


@typing.final
@dataclasses.dataclass(frozen=True, kw_only=True, slots=True)
class Violation:
    line_number: int
    column_number: int
    violation_code: ViolationCodeItem

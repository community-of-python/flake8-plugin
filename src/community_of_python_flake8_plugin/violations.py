from __future__ import annotations
import dataclasses
import typing


if typing.TYPE_CHECKING:
    from .violation_codes import ViolationCodeItem


@typing.final
@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)
class Violation:  # noqa: COP014
    line_number: int
    column_number: int
    violation_code: ViolationCodeItem

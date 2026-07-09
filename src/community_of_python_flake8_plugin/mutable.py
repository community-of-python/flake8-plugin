from __future__ import annotations
import typing


_ValueType = typing.TypeVar("_ValueType")

if typing.TYPE_CHECKING:
    # For type checkers Mutable[T] is just T with an extra marker; bare Mutable is also accepted.
    Mutable: typing.TypeAlias = typing.Annotated[_ValueType, "mutable"]  # noqa: COP005
else:

    @typing.final
    class _MutableMarker:
        def __getitem__(self, item_value: _ValueType) -> _ValueType:
            return item_value

    Mutable = _MutableMarker()  # noqa: COP005,COP017

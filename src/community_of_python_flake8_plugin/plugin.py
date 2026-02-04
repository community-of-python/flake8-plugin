from __future__ import annotations
import typing


if typing.TYPE_CHECKING:
    import ast
    from collections.abc import Iterable

    from community_of_python_flake8_plugin.violations import Violation


class PluginCheck(typing.Protocol):
    violations: list[Violation]

    def visit(self, node: ast.AST) -> None: ...


@typing.final
class CommunityOfPythonFlake8Plugin:
    name = "community-of-python-flake8-plugin"  # noqa: COP004
    version = "0.1.27"  # noqa: COP004

    def __init__(self, tree: ast.AST) -> None:  # noqa: COP004
        self.ast_tree = tree

    def run(self) -> Iterable[tuple[int, int, str, type[object]]]:  # noqa: COP004
        discovered_checks: list[PluginCheck] = ...
        for one_check in discovered_checks:
            for one_violation in one_check.violations:
                violation_message = f"{one_violation.violation_code.code} {one_violation.violation_code.description}"
                yield one_violation.line_number, one_violation.column_number, violation_message, type(self)

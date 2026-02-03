from __future__ import annotations
import typing


if typing.TYPE_CHECKING:
    import ast
    from collections.abc import Iterable


from community_of_python_flake8_plugin.checks import execute_all_validations


@typing.final
class CommunityOfPythonFlake8Plugin:
    name = "community-of-python-flake8-plugin"  # noqa: COP004
    version = "0.1.27"  # noqa: COP004

    def __init__(self, tree: ast.AST) -> None:  # noqa: COP004
        self.ast_tree = tree

    def run(self) -> Iterable[tuple[int, int, str, type[object]]]:  # noqa: COP004
        violations_list: typing.Final = execute_all_validations(self.ast_tree)
        for violation in violations_list:
            violation_message = (
                f"{violation.violation_code.value['code']} {violation.violation_code.value['description']}"
            )
            yield violation.line_number, violation.column_number, violation_message, type(self)

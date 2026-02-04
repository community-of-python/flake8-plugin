from __future__ import annotations
import importlib
import pkgutil
import typing

import community_of_python_flake8_plugin.checks as checks_module


if typing.TYPE_CHECKING:
    import ast
    from collections.abc import Iterable

    from community_of_python_flake8_plugin.violations import Violation


class PluginCheckProtocol(typing.Protocol):
    violations: list[Violation]

    def __init__(self, tree: ast.AST) -> None: ...  # noqa: COP004G
    def visit(self, node: ast.AST) -> None: ...  # noqa: COP004F,COP004G,COP008


@typing.final
class CommunityOfPythonFlake8Plugin:
    plugin_name: typing.Final[str] = "community-of-python-flake8-plugin"
    plugin_version: typing.Final[str] = "0.1.27"

    def __init__(self, tree: ast.AST) -> None:  # noqa: COP004G
        self.ast_syntax_tree: typing.Final[ast.AST] = tree

    def run(self) -> Iterable[tuple[int, int, str, type[object]]]:  # noqa: COP004F
        checks_collection: typing.Final[list[PluginCheckProtocol]] = []

        for _, module_name, _ in pkgutil.iter_modules(checks_module.__path__):
            if module_name == "__init__":
                continue

            module_full_name = f"{checks_module.__name__}.{module_name}"  # noqa: COP007
            imported_module = importlib.import_module(module_full_name)

            for attribute_name in dir(imported_module):
                attribute = getattr(imported_module, attribute_name)
                if isinstance(attribute, type) and attribute_name.endswith("Check") and hasattr(attribute, "visit"):
                    check_instance = attribute(self.ast_syntax_tree)
                    check_instance.visit(self.ast_syntax_tree)
                    checks_collection.append(check_instance)

        for check_instance in checks_collection:
            for violation in check_instance.violations:
                message_text = f"{violation.violation_code.code} {violation.violation_code.description}"
                yield violation.line_number, violation.column_number, message_text, type(self)

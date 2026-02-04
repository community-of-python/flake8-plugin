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
    name = "community-of-python-flake8-plugin"  # noqa: COP004V
    version = "0.1.27"  # noqa: COP004V

    def __init__(self, tree: ast.AST) -> None:  # noqa: COP004G
        self.ast_syntax_tree = tree

    def run(self) -> Iterable[tuple[int, int, str, type[object]]]:  # noqa: COP004F
        plugin_checks_collection = []
        for _, module_name, _ in pkgutil.iter_modules(checks_module.__path__):
            if module_name == "__init__":
                continue
            full_module_name = f"{checks_module.__name__}.{module_name}"
            imported_module = importlib.import_module(full_module_name)

            for attribute_name in dir(imported_module):
                attribute = getattr(imported_module, attribute_name)
                if isinstance(attribute, type) and attribute_name.endswith("Check") and hasattr(attribute, "visit"):
                    instance = attribute(self.ast_syntax_tree)
                    instance.visit(self.ast_syntax_tree)
                    plugin_checks_collection.append(instance)

        for check_instance in plugin_checks_collection:
            for violation_record in check_instance.violations:
                violation_message = (
                    f"{violation_record.violation_code.code} {violation_record.violation_code.description}"
                )
                yield violation_record.line_number, violation_record.column_number, violation_message, type(self)

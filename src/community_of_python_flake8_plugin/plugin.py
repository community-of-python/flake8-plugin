from __future__ import annotations
import importlib
import pkgutil
import typing


if typing.TYPE_CHECKING:
    import ast
    from collections.abc import Iterable

    from community_of_python_flake8_plugin.violations import Violation


class PluginCheckProtocol(typing.Protocol):
    violations: list[Violation]

    def visit(self, node: ast.AST) -> None: ...  # noqa: COP004F,COP004G,COP008


@typing.final
class CommunityOfPythonFlake8Plugin:
    plugin_name = "community-of-python-flake8-plugin"
    plugin_version = "0.1.27"

    def __init__(self, tree: ast.AST) -> None:  # noqa: COP004G
        self.ast_syntax_tree = tree

    def run(self) -> Iterable[tuple[int, int, str, type[object]]]:  # noqa: COP004F
        # Import checks module dynamically
        import community_of_python_flake8_plugin.checks as checks_module

        # List to store instantiated checks
        plugin_checks_collection = []

        # Discover and instantiate all check classes
        for _, module_name, _ in pkgutil.iter_modules(checks_module.__path__):
            if module_name == "__init__":
                continue

            # Import the module
            full_module_name = f"{checks_module.__name__}.{module_name}"
            imported_module = importlib.import_module(full_module_name)

            # Find all check classes in the module
            for attribute_name in dir(imported_module):
                attribute = getattr(imported_module, attribute_name)
                if isinstance(attribute, type) and attribute_name.endswith("Check") and hasattr(attribute, "visit"):
                    # Instantiate all checks with no parameters
                    try:
                        instance = attribute()

                        # Pass the AST tree to checks that have a set_syntax_tree method
                        if hasattr(instance, "set_syntax_tree"):
                            instance.set_syntax_tree(self.ast_syntax_tree)

                        instance.visit(self.ast_syntax_tree)
                        plugin_checks_collection.append(instance)
                    except Exception:
                        # Skip checks that fail to instantiate
                        continue

        # Yield all violations
        for check_instance in plugin_checks_collection:
            for violation_record in check_instance.violations:
                violation_message = (
                    f"{violation_record.violation_code.code} {violation_record.violation_code.description}"
                )
                yield violation_record.line_number, violation_record.column_number, violation_message, type(self)

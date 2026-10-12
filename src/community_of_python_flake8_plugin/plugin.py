from __future__ import annotations
import importlib
import importlib.metadata
import pathlib
import pkgutil
import typing

import community_of_python_flake8_plugin.checks as checks_module
from community_of_python_flake8_plugin.checks import module_import_many_names


if typing.TYPE_CHECKING:
    import argparse
    import ast
    from collections.abc import Iterable

    from community_of_python_flake8_plugin.violations import Violation


class PluginCheckProtocol(typing.Protocol):
    @property
    def violations(self) -> list[Violation]: ...

    def __init__(self, *, syntax_tree: ast.AST) -> None: ...
    def visit(self, node: ast.AST) -> None: ...  # noqa: COP007,COP006,COP012


@typing.final
class CommunityOfPythonFlake8Plugin:
    name: typing.Final[str] = str(pathlib.Path(__file__).parent.name)  # noqa: COP004
    version: typing.Final[str] = importlib.metadata.version(name)  # noqa: COP004
    cop001_enabled: typing.ClassVar[bool] = False

    def __init__(self, tree: ast.AST, filename: str = "stdin") -> None:  # noqa: COP006
        self.ast_syntax_tree: typing.Final[ast.AST] = tree
        self.source_filename: typing.Final = filename

    @classmethod
    def parse_options(cls, parsed_options: argparse.Namespace) -> None:
        cls.cop001_enabled = "COP001" in (
            *(parsed_options.select or []),
            *(parsed_options.extend_select or []),
        )

    def run(self) -> Iterable[tuple[int, int, str, type[object]]]:  # noqa: COP007
        for one_check_instance in self._collect_checks():
            for one_violation in one_check_instance.violations:
                yield (
                    one_violation.line_number,
                    one_violation.column_number,
                    f"{one_violation.violation_code.code} {one_violation.violation_code.description}",
                    type(self),
                )

    def _collect_checks(self) -> list[PluginCheckProtocol]:
        checks_collection: typing.Final = []
        for _, one_module_name, _ in pkgutil.iter_modules(checks_module.__path__):
            if one_module_name == "module_import_many_names" and not self.cop001_enabled:
                continue
            imported_module = importlib.import_module(f"{checks_module.__name__}.{one_module_name}")

            for one_attribute_name in dir(imported_module):
                attribute = getattr(imported_module, one_attribute_name)
                if isinstance(attribute, type) and one_attribute_name.endswith("Check") and hasattr(attribute, "visit"):
                    check_instance: PluginCheckProtocol = (
                        module_import_many_names.ModuleImportManyNamesCheck(
                            syntax_tree=self.ast_syntax_tree, filename=self.source_filename
                        )
                        if attribute is module_import_many_names.ModuleImportManyNamesCheck
                        else typing.cast("type[PluginCheckProtocol]", attribute)(syntax_tree=self.ast_syntax_tree)
                    )
                    check_instance.visit(self.ast_syntax_tree)
                    checks_collection.append(check_instance)
        return checks_collection

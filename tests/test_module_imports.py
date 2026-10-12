from __future__ import annotations
import ast
import importlib.machinery
import importlib.util
import os
import pathlib
import subprocess
import sys
import typing

import pytest

from community_of_python_flake8_plugin.checks import module_import_many_names
from community_of_python_flake8_plugin.plugin import CommunityOfPythonFlake8Plugin


SYMBOL_SOURCE: typing.Final = "class FirstClass: pass\nclass SecondClass: pass\nclass ThirdClass: pass\n"


def collect_import_codes(*, source_code: str, filename: pathlib.Path) -> list[str]:  # noqa: COP006
    return [
        one_result[2].split()[0]
        for one_result in CommunityOfPythonFlake8Plugin(ast.parse(source_code), str(filename)).run()
        if one_result[2].startswith("COP001")
    ]


@pytest.mark.parametrize(
    ("source_code", "expected_codes"),
    [
        ("from fixture_module import FirstClass, SecondClass, ThirdClass", ["COP001"]),
        ("from fixture_module import FirstClass as RenamedClass, SecondClass, ThirdClass", ["COP001"]),
        ("from fixture_module import FirstClass, SecondClass", []),
        ("from fixture_module import FirstClass, SecondClass, UnknownClass", []),
        ("from unavailable_package import alpha, beta, gamma", []),
        ("from .fixture_module import FirstClass, SecondClass, ThirdClass", []),
        ("from fixture_module import FirstClass, SecondClass, ThirdClass\n__all__ = ['unrelated_export']", []),
        ("from fixture_module import FirstClass, SecondClass, ThirdClass\n__all__: list[str] = []", []),
    ],
)
def test_classify_source_symbols(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, source_code: str, expected_codes: list[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fixture_module.py").write_text(SYMBOL_SOURCE)
    assert collect_import_codes(source_code=source_code, filename=tmp_path / "consumer.py") == expected_codes


@pytest.mark.parametrize(
    "source_code",
    [
        "from importlib import resources, metadata, util",
        "from collections.abc import Iterable, Iterator, Mapping",
        "from __future__ import annotations, division, print_function",
        "from os import name, environ, getcwd",
        "from xml.etree.ElementTree import Element, SubElement, tostring",
    ],
)
def test_preserve_stdlib_imports(source_code: str, tmp_path: pathlib.Path) -> None:
    assert collect_import_codes(source_code=source_code, filename=tmp_path / "consumer.py") == []


@pytest.mark.parametrize("initializer", ["", "raise RuntimeError('must not execute')\n"])
def test_skip_module_imports(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, initializer: str) -> None:  # noqa: COP006
    monkeypatch.chdir(tmp_path)
    package_directory: typing.Final = tmp_path / "fixture_package"
    package_directory.mkdir()
    (package_directory / "__init__.py").write_text(initializer)
    for one_module in ("alpha", "beta", "gamma"):
        (package_directory / f"{one_module}.py").write_text("raise RuntimeError('must not execute')\n")
    assert (
        collect_import_codes(
            source_code="from fixture_package import alpha, beta, gamma", filename=tmp_path / "consumer.py"
        )
        == []
    )


def test_detect_mixed_imports(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    package_directory: typing.Final = tmp_path / "fixture_package"
    package_directory.mkdir()
    (package_directory / "__init__.py").write_text(SYMBOL_SOURCE)
    (package_directory / "submodule.py").write_text("")
    assert collect_import_codes(
        source_code="from fixture_package import submodule, FirstClass, SecondClass, ThirdClass",
        filename=tmp_path / "consumer.py",
    ) == ["COP001"]


def test_never_execute_package_code(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    package_directory: typing.Final = tmp_path / "fixture_package"
    package_directory.mkdir()
    (package_directory / "__init__.py").write_text(
        "from pathlib import Path\n"
        "Path(__file__).with_name('executed').touch()\n"
        "raise RuntimeError('must not execute')\n"
    )
    (package_directory / "definitions.py").write_text(SYMBOL_SOURCE + "raise RuntimeError('must not execute')\n")

    def reject_runtime_lookup(*arguments: object, **parameters: object) -> typing.NoReturn:  # noqa: ARG001
        raise AssertionError("runtime import lookup must not be used")

    monkeypatch.setattr(importlib.util, "find_spec", reject_runtime_lookup)
    monkeypatch.setattr(importlib.machinery.PathFinder, "find_spec", reject_runtime_lookup)
    check_instance: typing.Final = module_import_many_names.ModuleImportManyNamesCheck(
        syntax_tree=ast.parse("from fixture_package.definitions import FirstClass, SecondClass, ThirdClass")
    )
    check_instance.visit(check_instance.syntax_tree)
    assert [one_violation.violation_code.code for one_violation in check_instance.violations] == ["COP001"]
    assert not (package_directory / "executed").exists()
    assert "fixture_package" not in sys.modules


@pytest.mark.parametrize(
    "source_code",
    [
        SYMBOL_SOURCE + "\ndef __getattr__(attribute_name): return None\n",
        SYMBOL_SOURCE + "\n__path__ = calculate_search_path()\n",
        SYMBOL_SOURCE + "\nFirstClass = calculate_dynamic_export()\n",
        SYMBOL_SOURCE + "\nfrom dynamic_package import export as FirstClass\n",
        "not valid python!",
    ],
)
def test_skip_dynamic_or_invalid_modules(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, source_code: str
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fixture_module.py").write_text(source_code)
    assert (
        collect_import_codes(
            source_code="from fixture_module import FirstClass, SecondClass, ThirdClass",
            filename=tmp_path / "consumer.py",
        )
        == []
    )


@pytest.mark.parametrize("source_suffix", [".py", ".pyi"])
def test_detect_installed_module(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, source_suffix: str) -> None:
    installed_directory: typing.Final = tmp_path / "site-packages"
    installed_directory.mkdir()
    (installed_directory / f"fixture_module{source_suffix}").write_text(SYMBOL_SOURCE)
    monkeypatch.syspath_prepend(str(installed_directory))
    assert collect_import_codes(
        source_code="from fixture_module import FirstClass, SecondClass, ThirdClass", filename=tmp_path / "consumer.py"
    ) == ["COP001"]


def test_skip_native_module(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fixture_module.so").write_bytes(b"not an executable module")
    (tmp_path / "fixture_module.py").write_text(SYMBOL_SOURCE)
    assert (
        collect_import_codes(
            source_code="from fixture_module import FirstClass, SecondClass, ThirdClass",
            filename=tmp_path / "consumer.py",
        )
        == []
    )


def test_skip_dynamic_parent_paths(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    package_directory: typing.Final = tmp_path / "fixture_package"
    package_directory.mkdir()
    (package_directory / "__init__.py").write_text("__path__ = calculate_dynamic_path()\n")
    (package_directory / "definitions.py").write_text(SYMBOL_SOURCE)
    assert (
        collect_import_codes(
            source_code="from fixture_package.definitions import FirstClass, SecondClass, ThirdClass",
            filename=tmp_path / "consumer.py",
        )
        == []
    )


def test_never_evaluate_pth_files(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "fixture_module.py").write_text(SYMBOL_SOURCE)
    (tmp_path / "fixture.pth").write_text("import pathlib; pathlib.Path('executed').touch()\n")
    assert collect_import_codes(
        source_code="from fixture_module import FirstClass, SecondClass, ThirdClass", filename=tmp_path / "consumer.py"
    ) == ["COP001"]
    assert not (tmp_path / "executed").exists()


@pytest.mark.parametrize("source_layout", ["flat", "src", "namespace"])
def test_compare_flake8_entrypoints(tmp_path: pathlib.Path, source_layout: str) -> None:
    project_directory: typing.Final = tmp_path / "project"
    project_directory.mkdir()
    (project_directory / "pyproject.toml").write_text("[project]\nname = 'fixture-project'\nversion = '0.0.0'\n")
    package_directory: typing.Final = (
        project_directory / "src" / "fixture_package"
        if source_layout == "src"
        else project_directory / "fixture_package"
    )
    package_directory.mkdir(parents=True)
    if source_layout != "namespace":
        (package_directory / "__init__.py").write_text("raise RuntimeError('must not execute')\n")
    (package_directory / "definitions.py").write_text(SYMBOL_SOURCE)
    consumer_path: typing.Final = package_directory / "consumer.py"
    consumer_path.write_text("from fixture_package.definitions import FirstClass, SecondClass, ThirdClass\n")
    console_path: typing.Final = pathlib.Path(sys.executable).parent / "flake8"
    runtime_environment: typing.Final = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    command_outputs: typing.Final = []
    # Run outside the project so filename-based roots are exercised as well.
    for one_command in ([str(console_path)], [sys.executable, "-m", "flake8"]):
        completed_process = subprocess.run(  # noqa: S603
            [*one_command, "--isolated", "--select=COP001", "--jobs=1", str(consumer_path)],
            cwd=tmp_path,
            env=runtime_environment,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed_process.returncode == 1, completed_process.stderr
        assert "COP001" in completed_process.stdout
        command_outputs.append(completed_process.stdout)
    assert command_outputs[0] == command_outputs[1]

from __future__ import annotations
import ast

import pytest

from community_of_python_flake8_plugin.plugin import CommunityOfPythonFlake8Plugin


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP002: Import standard library modules as whole modules
        ("from os import name", ["COP002"]),
        # COP002: Even resources submodule should be imported as whole
        ("from importlib.resources import files", ["COP002"]),
        # No violation: __future__ imports are allowed
        ("from __future__ import annotations", []),
        # No violation: third-party imports are fine
        ("from third_party import widget", []),
        # No violation: collections.abc is whitelisted
        ("from collections.abc import AsyncIterator", []),
        # COP002: TypedDict should be imported from typing module, not via from import
        (
            "from typing import TypedDict, NotRequired\n\n"
            "UnsubscribeHeaders = TypedDict(\n"
            "    'UnsubscribeHeaders',\n"
            "    {\n"
            "        'id': str,\n"
            "        'content-length': NotRequired[str],\n"
            "    },\n"
            ")",
            ["COP002"],
        ),
        # No violation: TypedDict imported correctly from typing module
        (
            "import typing\n\n"
            "UnsubscribeHeaders = typing.TypedDict(\n"
            "    'UnsubscribeHeaders',\n"
            "    {\n"
            "        'id': str,\n"
            "        'content-length': typing.NotRequired[str],\n"
            "    },\n"
            ")",
            [],
        ),
    ],
)
def test_import_stdlib_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)

@pytest.mark.skip("disabled")
@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP001: Use module import when importing more than two names
        ("from x import a, b, c", ["COP001"]),
        # COP001: Importing more than two names from third party (but settings exempt)
        ("from my_project.settings import A, B, C", []),
        # No violation: importlib resources submodules are allowed
        ("from importlib import resources", []),
        ("from importlib import metadata", []),
        # No violation: unittest mock is allowed
        ("from unittest import mock", []),
        # No violation: Multiple imports from stdlib subpackage
        ("from importlib import resources, simple, util", []),
        # No violation: When __all__ is defined, more than two imports are allowed
        ("__all__ = ['a', 'b', 'c']\nfrom x import a, b, c", []),
    ],
)
def test_import_many_names_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP003: Avoid explicit scalar type annotations with literal values
        ("value: str = 'hello'", ["COP003"]),
        # No violation: Scalar annotation is fine with non-literal value
        ("value: int = do_something()", []),
        # COP003: Even with Final, scalar annotation with literal is flagged
        ("value: typing.Final[int] = 1", ["COP003"]),
        # Note: self.value annotations are in method bodies, not class bodies, so no violation
        ("self.value: str = 'hello'", []),
        # No violation: Assignment without annotation doesn't trigger annotation checks
        ("value = 1", []),
    ],
)
def test_type_annotation_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP004: Attribute name too short
        # Also triggers COP008 (class name too short) and COP012 (missing final decorator)
        ("class MyClass:\n    a: int = 1", ["COP004", "COP008", "COP012"]),
        # COP005: Variable name too short
        # Also triggers COP007 (function name too short), COP009 (function not a verb), COP011 (temporary variable)
        ("def example():\n    x = 1\n    return x", ["COP005", "COP007", "COP009", "COP011"]),
        # COP006: Argument name too short (regular function)
        ("def fetch_item(user: int) -> int:\n    return user", ["COP006"]),
        # COP006: Argument name too short (method with self)
        ("def fetch_item(self, user: int) -> int:\n    return user", ["COP006"]),
        # COP006: Argument name too short (class method with cls)
        ("def fetch_item(cls, user: int) -> int:\n    return user", ["COP006"]),
        # COP006: Vararg name too short
        ("def fetch_item(*args: int) -> int:\n    return 1", ["COP006"]),
        # COP006: Kwargs name too short
        ("def fetch_item(**kwargs: int) -> int:\n    return 1", ["COP006"]),
        # COP007: Function name too short
        # Also triggers COP009 (function not a verb)
        ("def calc() -> int:\n    return 1", ["COP007", "COP009"]),
        # COP008: Class name too short
        # Also triggers COP012 (missing final decorator)
        ("class Abc:\n    value: int = 1", ["COP008", "COP012"]),
        # COP008: Single-letter class name (but single uppercase letters are exempt)
        # Only triggers COP004 (attribute name too short) and COP012 (missing final decorator)
        ("class C:\n    a: int = 1", ["COP004", "COP012"]),
        # No violation: Test classes are exempt
        ("class TestExample:\n    value: int", []),
        # No violation: Uppercase constants are exempt
        ("VALUE = 10", []),
        # No violation: main function is exempt
        ("def main() -> None:\n    return None", []),
        # No violation: Test functions are exempt
        ("def test_example() -> None:\n    return None", []),
        # No violation: pytest fixture is exempt from naming rules
        ("import pytest\n\n@pytest.fixture\ndef data():\n    return 1", []),
        # No violation: underscore variable is ignored
        ("_ = 1", []),
        # No violation: underscore attribute is ignored, but still need final decorator
        ("class ExampleClass:\n    _ = 1", ["COP012"]),
        # COP007: Function name must be a verb
        ("def total_value() -> int:\n    return 1", ["COP009"]),
        # No violation: get_ prefix is allowed for sync functions
        ("def get_user_data() -> str:\n    return 'value'", []),
        # COP010: Avoid get_ prefix in async function names
        ("async def get_user_data() -> str:\n    return 'value'", ["COP010"]),
        # COP009: Function name must be a verb (even with mutable params)
        ("def fill_values(values: list[int]) -> None:\n    values[0] = 1", ["COP009"]),
        # No violation: pytest fixture annotation is whitelisted
        (
            "import pytest\n@pytest.fixture\ndef some_fixture(arg: pytest.fixture): pass",
            [],
        ),
        # No violation: pytest fixture annotation (imported) is whitelisted
        (
            "from pytest import fixture\n@fixture\ndef some_fixture(arg: fixture): pass",
            [],
        ),
        # COP009: faker.Faker annotation doesn't exempt function naming rules
        (
            "import faker\ndef some_func(arg: faker.Faker): pass",
            ["COP009"],
        ),
        # No violation: Non-fixture decorator doesn't trigger fixture check
        (
            "import functools\n@functools.lru_cache()\ndef func(): pass",
            ["COP007", "COP009"],
        ),
        # COP009: Non-whitelisted annotation doesn't exempt function naming rules
        # Also triggers COP007 (function name too short) and COP006 (argument name too short)
        (
            "def func(user: CustomType): pass",
            ["COP007", "COP006", "COP009"],
        ),
        # COP009: Subscript annotation doesn't exempt function naming rules
        # Also triggers COP007 (function name too short) and COP006 (argument name too short)
        (
            "def func(user: List[int]): pass",
            ["COP007", "COP006", "COP009"],
        ),
        # No violation: Unannotated argument doesn't trigger annotation checks
        # Also triggers COP007 (function name too short) and COP006 (argument name too short)
        (
            "def func(user): pass",
            ["COP007", "COP006", "COP009"],
        ),
        # COP009: Faker annotation doesn't exempt function naming rules
        (
            "from faker import Faker\ndef some_func(arg: Faker): pass",
            ["COP009"],
        ),
    ],
)
def test_naming_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP011: Avoid temporary variables used only once
        (
            "def fetch_value() -> int:\n    result_value = 1\n    another_value = result_value\n    "
            "return another_value",
            ["COP011"],
        ),
        # No violation: Variable used multiple times
        ("def fetch_item(values: list[int]) -> int:\n    return values[0]", []),
        # No violation: Variable not used
        ("def fetch_item(values: list[int]) -> int:\n    ...", []),
        # No violation: Variable used in conditional
        (
            "def fetch_item(values: list[int]) -> int | None:\n    if len(values) > 0:\n        return values[0]\n    "
            "return None",
            [],
        ),
        # No violation: Variable used in loop
        ("def fetch_item():\n    for _, one_value in values: print(f'{one_value}')", []),
    ],
)
def test_variable_usage_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP012: Classes should be marked typing.final
        (
            "class FinalClass:\n    value: int\n    def __init__(self, value: int) -> None:\n        "
            "self.value = value",
            ["COP012"],
        ),
        # COP012: Classes inheriting from BaseModel now require final decorator
        ("from pydantic import BaseModel\nclass MyBaseModel(BaseModel): ...", ["COP012"]),
        ("import pydantic\nclass MyBaseModel(pydantic.BaseModel): ...", ["COP012"]),
        # COP012: Classes inheriting from RootModel now require final decorator
        ("from pydantic import RootModel\nclass MyRootModel(RootModel): ...", ["COP012"]),
        # COP012: Classes inheriting from ModelFactory now require final decorator
        (
            "from polyfactory.factories.pydantic_factory import ModelFactory\nclass MyModelFactory(ModelFactory): ...",
            ["COP012"],
        ),
        # COP012: Exception classes now require final decorator
        (
            "import dataclasses\n\n@dataclasses.dataclass\nclass ExampleError(ValueError):\n    value: int\n",
            ["COP012"],
        ),
        # COP012: Inheriting dataclasses now require final decorator
        (
            "import dataclasses\n\n@dataclasses.dataclass\nclass ExampleChild(Example):\n    value: int\n",
            ["COP012", "COP014"],
        ),
        # COP012: Classes inheriting from ModelFactory now require final decorator (with methods)
        (
            "from polyfactory.factories.pydantic_factory import ModelFactory\n"
            "class MyModelFactory(ModelFactory):\n"
            "    def fn():\n"
            "        pass",
            ["COP012"],
        ),
    ],
)
def test_class_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP013: Wrap module dictionaries with types.MappingProxyType
        ("values = {'key': 'value'}", ["COP013"]),
        # No violation: Dictionary wrapped in MappingProxyType
        ("import types\nvalues = types.MappingProxyType({'key': 'value'})", []),
        # No violation: Simple integer assignment
        ("value = 1", []),
    ],
)
def test_module_level_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP014: Dataclass with missing required args
        # Also triggers COP004 for attributes being too short
        (
            "import dataclasses\n\n@dataclasses.dataclass\nclass Example:\n    value: int\n    name: str\n",
            ["COP004", "COP008", "COP012", "COP014"],
        ),
        # COP012: Dataclass with correct config but short name and missing final decorator
        (
            "import dataclasses\n\n"
            "@dataclasses.dataclass(kw_only=True, slots=True, frozen=True)\n"
            "class Example:\n"
            "    value: int\n",
            ["COP008", "COP012"],
        ),
        # No violation: Class inheriting from attribute-based whitelisted base
        # Still needs final decorator
        (
            "import pydantic\nclass MyModelClass(pydantic.BaseModel):\n    value: int\n",
            ["COP012"],
        ),
        # No violation: Direct test of attribute-based inheritance (hits lines 51-52)
        (
            "import polyfactory.factories.pydantic_factory\n"
            "class MyFactoryClass(polyfactory.factories.pydantic_factory.ModelFactory):\n"
            "    pass",
            ["COP012"],
        ),
        # COP014: Dataclass with init=False still needs slots and frozen
        (
            "import dataclasses\n\n@dataclasses.dataclass(init=False)\nclass Example:\n    value: int\n",
            ["COP008", "COP012", "COP014"],
        ),
        # No violation: Attribute in whitelisted parent class is exempt
        # Still needs final decorator
        (
            "from pydantic import BaseModel\nclass MyModelClass(BaseModel):\n    value: int\n",
            ["COP012"],
        ),
        # No violation: Attribute in RootModel subclass is exempt
        # Still needs final decorator
        (
            "from pydantic import RootModel\nclass MyModelClass(RootModel):\n    value: int\n",
            ["COP012"],
        ),
        # No violation: Variable with non-standard assignment pattern
        # Still needs final decorator
        (
            "class ExampleClass:\n    value = 1 if True else 2",
            ["COP012"],
        ),
        # Direct test: Attribute in whitelisted class should hit early return (line 101)
        (
            "from pydantic import BaseModel\n"
            "class MyModelClass(BaseModel):\n"
            "    short_attr: int = 1",  # This should NOT trigger COP004 due to early return
            ["COP012"],
        ),
        # Test for fallback violation code assignment (line 110)
        (
            "class ExampleClass:\n    value = 1\n    # This tests the fallback path in validate_name_length",
            ["COP012"],
        ),
    ],
)
def test_dataclass_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # Combined case: MyClass (short name), calc (short name), MyClass (not final)
        (
            "import functools\nclass MyClass:\n    @functools.cached_property\n    def calc(): pass",
            ["COP008", "COP007", "COP012"],
        ),
    ],
)
def test_combined_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [item[2].split(" ")[0] for item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()]  # noqa: COP011
    ) == sorted(expected_output)

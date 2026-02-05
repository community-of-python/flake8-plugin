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
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
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
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
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
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
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
        # No violation: pytest fixture with name parameter should be exempt from COP009
        (
            "import pytest\n@pytest.fixture(name='events')\ndef fixture_events() -> list[dict]:\n    return []",
            [],
        ),
        # No violation: property decorator should exempt function from COP009 (but not COP007 for name length)
        (
            "class ExampleClass:\n    @property\n    def calculator(): pass",
            ["COP012"],
        ),
        # No violation: property() decorator call should exempt function from COP009 (but not COP007)
        (
            "class ExampleClass:\n    @property()\n    def calculator(): pass",
            ["COP012"],
        ),
        # No violation: cached_property decorator should exempt function from COP009 (but not COP007)
        (
            "import functools\nclass ExampleClass:\n    @functools.cached_property\n    def calculator(): pass",
            ["COP012"],
        ),
        # No violation: cached_property() decorator call should exempt function from COP009 (but not COP007)
        (
            "import functools\nclass ExampleClass:\n    @functools.cached_property()\n    def calculator(): pass",
            ["COP012"],
        ),
        # No violation: ModelFactory methods should be exempt from COP009
        (
            "from polyfactory.factories.pydantic_factory import ModelFactory\n"
            "class MyFactory(ModelFactory):\n    def calculator(self): pass",
            ["COP012"],
        ),
        # No violation: ModelFactory generic methods should be exempt from COP009
        (
            "from polyfactory.factories.pydantic_factory import ModelFactory\nimport some_module\n"
            "class MyFactory(ModelFactory[some_module.SomeClass]):\n    def calculator(self): pass",
            ["COP012"],
        ),
        # No violation: ModelFactory classmethod should be exempt from COP009
        (
            "from polyfactory.factories.pydantic_factory import ModelFactory\n"
            "class MyFactory(ModelFactory):\n    @classmethod\n    def create(cls): pass",
            ["COP012"],
        ),
        # No violation: ModelFactory generic classmethod should be exempt from COP009
        (
            "from polyfactory.factories.pydantic_factory import ModelFactory\nimport some_module\n"
            "class MyFactory(ModelFactory[some_module.SomeClass]):\n    @classmethod\n    def create(cls): pass",
            ["COP012"],
        ),
        # No violation: cached_property imported directly should exempt function from COP009
        # (but triggers COP002 for import style)
        (
            "from functools import cached_property\n"
            "class ExampleClass:\n    @cached_property\n    def calculator(self): pass",
            ["COP002", "COP012"],
        ),
        # No violation: cached_property() imported directly should exempt function from COP009
        # (but triggers COP002)
        (
            "from functools import cached_property\n"
            "class ExampleClass:\n    @cached_property()\n    def calculator(self): pass",
            ["COP002", "COP012"],
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
        # COP005: Local variables in methods should trigger variable rule, not attribute rule
        (
            "class ExampleClass:\n    def idx_after_latest_restart(self) -> int:\n        "
            '"""Return the idx of the most recent restart in the list of events."""\n        '
            "idx = 0\n        return idx",
            ["COP012", "COP009", "COP005", "COP011"],
        ),
        # COP004 and COP005: Class attributes should trigger attribute rule, local variables should trigger variable rule
        (
            "class ExampleClass:\n    idx = 0\n    def method(self) -> int:\n        "
            '"""Return the idx of the most recent restart."""\n        '
            "idx = 0\n        return idx",
            ["COP012", "COP009", "COP004", "COP005", "COP007", "COP011"],
        ),
        # COP005: Variables outside classes in functions should trigger variable rule
        (
            "def process_events() -> int:\n    "
            '"""Process events and return index of latest restart."""\n    '
            "idx = 0\n    return idx",
            ["COP005", "COP011"],
        ),
    ],
)
def test_naming_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP011: Avoid temporary variables used only once
        (
            "def fetch_value() -> int:\n    result_value = 1\n    another_value = result_value\n    "
            "return another_value",
            ["COP011", "COP011"],
        ),
        # COP011: Single-line assignment used immediately in next line
        (
            "def func():\n    a = 1\n    b = a + 1",
            ["COP005", "COP005", "COP007", "COP009", "COP011"],
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
        # No violation: Tuple unpacking with underscore variables
        ("def parse_module():\n    parent, _, _child = module_name.rpartition('.')\n    return parent", []),
        # No violation: Single-line assignment with intervening lines
        (
            "def func():\n    a = 1\n    # some things here\n    b = a + 1",
            ["COP005", "COP005", "COP007", "COP009"],
        ),
        # No violation: Multi-line assignment used immediately
        (
            "def func():\n    a = (\n        one_item for one_item\n        in lst\n    )\n    b = a[0]",
            ["COP005", "COP005", "COP007", "COP009"],
        ),
        # No violation: Tuple unpacking assignment
        (
            "def func():\n    a, b = (1, 2)\n    c = a + b",
            ["COP005", "COP007", "COP009"],
        ),
    ],
)
def test_variable_usage_validations(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
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
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
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
        # No violation: TypedDict annotation should be ignored (other violations are OK)
        (
            "import typing\nclass LatencyLabels(typing.TypedDict): ...\n"
            "PROMETHEUS_LABELS: typing.Final[LatencyLabels] = {}\n"
            "PROMETHEUS_LABELS_2: LatencyLabels = {}",
            [],
        ),
        # No violation: Other complex annotations should be ignored (other violations are OK)
        ("import typing\nMyType = typing.TypedDict('MyType', {'key': str})\nvalue: MyType = {}", []),
        # COP013 should still fire for explicit dict annotations
        ("value: dict = {'key': 'value'}", ["COP013"]),
        # COP013 should still fire for Final[dict] annotations
        ("import typing\nvalue: typing.Final[dict] = {'key': 'value'}", ["COP013"]),
        # COP013 should still fire for dict[key, value] annotations
        ("value: dict[str, str] = {'key': 'value'}", ["COP013"]),
        # COP013 should still fire for Final[dict[key, value]] annotations
        ("import typing\nvalue: typing.Final[dict[str, str]] = {'key': 'value'}", ["COP013"]),
    ],
)
def test_module_level_validations(input_source: str, expected_output: list[str]) -> None:
    assert [
        cop013_violation
        for cop013_violation in sorted(
            [
                violation_item[2].split(" ")[0]
                for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
            ]
        )
        if cop013_violation == "COP013"
    ] == expected_output


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
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
    ) == sorted(expected_output)


@pytest.mark.parametrize(
    ("input_source", "expected_output"),
    [
        # COP005: Module-level annotated assignment should be treated as variable, not attribute
        ("v: int = 1", ["COP005", "COP003"]),
        # COP005: Module-level Final assignment should be treated as variable, not attribute
        ("c: typing.Final = CreditStatementClient()", ["COP005"]),
        # COP004: Class-level annotated assignment should still be treated as attribute
        ("class ExampleClass:\n    a: int = 1", ["COP012", "COP004"]),
        # COP004: Class-level Final assignment should still be treated as attribute
        ("class ExampleClass:\n    client: typing.Final = CreditStatementClient()", ["COP012", "COP004"]),
        # COP005: With statement with short variable name should be flagged
        ("with open('file.txt') as f: pass", ["COP005"]),
        # No violation: With statement with long variable name
        ("with open('file.txt') as file_handle: pass", []),
        # COP005: Except handler with short variable name should be flagged
        ("try: pass\nexcept Exception as e: pass", ["COP005"]),
        # No violation: Except handler with long variable name
        ("try: pass\nexcept Exception as error_exc: pass", []),
        # COP006: Lambda with short argument names should be flagged
        ("func_long_name = lambda x: x * 2", ["COP006"]),
        # No violation: Lambda with long argument names
        ("func_long_name = lambda value: value * 2", []),
        # COP006: Lambda with multiple short arguments should be flagged
        ("func_long_name = lambda a, b: a + b", ["COP006", "COP006"]),
        # COP015: List comprehension without one_ prefix should be flagged (in addition to COP005)
        ("result_long_name = [v for v in some_list]", ["COP005", "COP015"]),
        # COP005: List comprehension with one_ prefix (still too short for general rule)
        ("result_long_name = [one_v for one_v in some_list]", ["COP005"]),
        # No violation: List comprehension with underscore (ignored)
        ("result_long_name = [_ for _ in some_list]", []),
        # COP005: List comprehension with tuple unpacking (prefix rule ignored, but length rule still applies)
        ("result_long_name = [x for x, y in pairs]", ["COP005", "COP005"]),
        # COP015: Set comprehension without one_ prefix should be flagged (in addition to COP005)
        ("result_long_name = {v for v in some_list}", ["COP005", "COP015"]),
        # COP005: Set comprehension with one_ prefix (vars still too short for general rule)
        ("result_long_name = {one_v for one_v in some_list}", ["COP005"]),
        # COP005+COP015: Dict comprehension without one_ prefix should be flagged
        ("result_long_name = {k: v for k, v in pairs}", ["COP005", "COP005", "COP015", "COP015"]),
        # COP005: Dict comprehension with one_ prefix (vars still too short for general rule)
        ("result_long_name = {one_k: one_v for one_k, one_v in pairs}", ["COP005", "COP005"]),
        # COP015: Generator expression without one_ prefix should be flagged (in addition to COP005)
        ("result_long_name = (v for v in some_list)", ["COP005", "COP015"]),
        # COP005: Generator expression with one_ prefix (vars still too short for general rule)
        ("result_long_name = (one_v for one_v in some_list)", ["COP005"]),
        # COP015: Regular for-loop without one_ prefix should be flagged
        ("for v in some_list: pass", ["COP015"]),
        # No violation: Regular for-loop with one_ prefix
        ("for one_v in some_list: pass", []),
        # No violation: Regular for-loop with underscore (ignored)
        ("for _ in some_list: pass", []),
        # No violation: Regular for-loop with tuple unpacking (ignored)
        ("for x, y in pairs: pass", []),
        # No violation: Regular for-loop with one_ prefix
        ("for one_x in some_list: pass", []),
    ],
)
def test_module_vs_class_level_assignments(input_source: str, expected_output: list[str]) -> None:
    assert sorted(
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
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
        [
            violation_item[2].split(" ")[0]
            for violation_item in CommunityOfPythonFlake8Plugin(ast.parse(input_source)).run()
        ]  # noqa: COP011
    ) == sorted(expected_output)

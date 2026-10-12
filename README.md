# Community of Python Flake8 Plugin

A Flake8 plugin that enforces the Community of Python's custom code style rules. This plugin provides a set of checks designed to promote consistent and idiomatic Python code within the community.

## Features

This plugin implements the following code style checks:

- **COP001**: Use module import when importing more than two names
- **COP002**: Import standard library modules as whole modules
- **COP003**: Avoid explicit scalar type annotations
- **COP004**: Attribute name must be at least 8 characters
- **COP005**: Variable name must be at least 8 characters
- **COP006**: Argument name must be at least 8 characters
- **COP007**: Function name must be at least 8 characters
- **COP008**: Class name must be at least 8 characters
- **COP009**: Function identifier must be a verb
- **COP010**: Avoid `get_` prefix in async function names
- **COP011**: Avoid temporary variables used only once
- **COP012**: Classes should be marked `typing.final`
- **COP013**: Wrap module dictionaries with `types.MappingProxyType`
- **COP014**: Use dataclasses with `kw_only=True`, `slots=True`, `frozen=True`
- **COP015**: For-loop variables must be prefixed with `one_`
- **COP016**: Add `*` or `/` when defining more than two regular arguments
- **COP017**: Avoid reassigning variables not annotated with `Mutable`

### COP001: import modules instead of many symbols

COP001 is off by default, including when selecting the `COP` prefix. Enable it
explicitly with `--extend-select=COP001`, `--select=COP001`, or in your Flake8 configuration:

```toml
[tool.flake8]
select = ["COP"]
extend-select = ["COP001"]
```

Use a module import when importing more than two statically identifiable symbols
from the same module. Aliases still count; imported submodules do not. Standard
library imports are handled exclusively by COP002, preserving its exceptions
for `__future__` and `collections.abc`.

COP001 reads Python source and stub files without executing inspected packages,
import hooks, native extensions, or `.pth` files. Search roots include the current
directory, the linted file's project directory and its `src` directory, and
existing interpreter search paths. Console-script and `python -m flake8`
invocations use the same project roots.

Detection is deliberately conservative: unavailable dependencies, dynamic
exports or package paths, re-exports, and opaque native modules are left
unchecked. Relative imports, imports from `.settings`, and files declaring
`__all__` retain their existing exemptions. Split imports are checked separately.

### COP017: immutable variables by default

Variables are treated as immutable: reassigning a name with `=` in the same scope is a violation. When reassignment is intended, allow it explicitly with the `Mutable` annotation on the first binding:

```python
from cop_extensions import Mutable

counter_value: Mutable[int] = 0
counter_value = compute_next(counter_value)  # OK

total_value = 0
total_value = compute_next(total_value)  # COP017
```

The `cop_extensions` package ships with the plugin distribution and has no runtime dependencies, so importing `Mutable` in production code does not pull in flake8. `Mutable` is matched by name, so any import source works (e.g. an in-house `typing_extensions.Mutable`). Augmented assignments (`+=`), for-loop variables, attribute and subscript targets, and names declared `global`/`nonlocal` are not checked.

## Installation

Install the plugin using `uv` (recommended). For linting, use the `flake8` extra:

```bash
uv add --dev "community-of-python-flake8-plugin[flake8]"
```

Or install via pip:

```bash
pip install "community-of-python-flake8-plugin[flake8]"
```

To use the `cop_extensions.Mutable` marker in production code, add the package without the extra — it has no runtime dependencies:

```bash
uv add community-of-python-flake8-plugin
```

## Usage

Run Flake8 with the plugin enabled:

```bash
uv run flake8 --select COP --exclude .venv .
```

Or if installed globally:

```bash
flake8 --select COP --exclude .venv .
```

## Configuration

Add the following to your `pyproject.toml` when using https://pypi.org/project/Flake8-pyproject/:

```toml
[tool.flake8]
select = ["COP"]
exclude = [".venv"]
```

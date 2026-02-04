# Community of Python Flake8 Plugin

A Flake8 plugin that enforces the Community of Python's custom code style rules. This plugin provides a set of checks designed to promote consistent and idiomatic Python code within the community.

## Features

This plugin implements the following code style checks:

- **COP001**: Use module import when importing more than two names
- **COP002**: Import standard library modules as whole modules
- **COP003**: Avoid explicit scalar type annotations
- **COP004A**: Attribute name must be at least 8 characters
- **COP004V**: Variable name must be at least 8 characters
- **COP004G**: Argument name must be at least 8 characters
- **COP004F**: Function name must be at least 8 characters
- **COP004C**: Class name must be at least 8 characters
- **COP005**: Function identifier must be a verb
- **COP006**: Avoid `get_` prefix in async function names
- **COP007**: Avoid temporary variables used only once
- **COP008**: Classes should be marked `typing.final`
- **COP009**: Wrap module dictionaries with `types.MappingProxyType`
- **COP010**: Use dataclasses with `kw_only=True`, `slots=True`, `frozen=True`

## Installation

Install the plugin using `uv` (recommended):

```bash
uv add --dev community-of-python-flake8-plugin
```

Or install via pip:

```bash
pip install community-of-python-flake8-plugin
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

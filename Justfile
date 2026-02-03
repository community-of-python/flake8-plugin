default: install lint test

install:
    uv sync

test *args:
    uv run --group test pytest {{args}}

lint:
    .venv/bin/ruff format
    .venv/bin/ruff check
    .venv/bin/auto-typing-final .
    .venv/bin/flake8 --select COP --exclude .venv . --show-source
    .venv/bin/mypy .

lint-ci:
    .venv/bin/ruff format
    .venv/bin/ruff check
    .venv/bin/auto-typing-final .
    .venv/bin/flake8 --select COP --exclude .venv . --show-source
    .venv/bin/mypy .

publish:
    rm -rf dist
    uv version $GITHUB_REF_NAME
    uv build
    uv publish --token $PYPI_TOKEN

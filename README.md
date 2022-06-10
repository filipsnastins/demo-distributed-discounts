# demo-distributed-discounts

Homework about distributed systems

## Installation

- Required software:

  - Python 3.9
  - [Python Poetry](https://python-poetry.org)
  - [PostgreSQL binaries](https://www.postgresql.org/download/)
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/)

- Update global Python packages

```
python -m pip install -U pip wheel setuptools
```

- Install dependencies

```
poetry install
```

- Activate Python virtual environment

```
poetry shell
```

- Install pre-commit hooks

```
pre-commit install
```

## Development and testing

- Helper commands from [scripts/dev_commands.py](scripts/dev_commands.py)

```
poetry run format/lint/test/test_cov_term/test_cov_html/test_ci
```

- Run all hooks at once

```
poetry run hooks
```

## TODO

- [ ]

# demo-distributed-discounts

- [demo-distributed-discounts](#demo-distributed-discounts)
  - [Installation](#installation)
    - [With Docker Compose and Poetry](#with-docker-compose-and-poetry)
  - [Development and testing](#development-and-testing)
  - [TODO](#todo)

Homework about distributed systems.

More documentation in [DOCS.md](DOCS.md)

## Installation

### With Docker Compose and Poetry

- Required software

  - Python 3.9 or higher
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - [Python Poetry](https://python-poetry.org)

- Start the app for development (with auto reload enabled)

  ```
  docker compose up
  ```

- After application start, database is refreshed with test data from [scripts/initial_data.py](scripts/initial_data.py)

  - Available `campaign_id` - 1 and 2
  - Generated 10'000 discount codes for each campaign.

- Start the app with gunicorn for concurrency testing (production mode)

  ```
  docker compose -f docker-compose.gunicorn.yml up
  ```

- (optional) To run auto tests with `pytest`, additionally install dependencies locally with Poetry

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

- [x] Documentation
- [x] How to start the app
- [ ] Presentation
- [x] Fetch a discount code
  - [x] POST, 201
  - [x] GET 200
  - [x] is_used flag
  - [x] 404 if campaign does not exist
  - [x] Authentication with fake JWT like token
  - [x] Decouple business logic from Flask route
  - [x] SELECT FOR UPDATE SKIP LOCKED for concurrent selects
  - [x] Send callback to the brand that code has been created
- [x] Generate a discount code. Brand wants to create X number of discount codes
  - [x] Generate job ID and simulate as if job was placed to the queue
  - [x] Create discounts codes asynchronously
  - [ ] Route for polling job status <-- not doing now

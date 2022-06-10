from subprocess import check_call


def hooks() -> None:
    check_call(["pre-commit", "run", "--all-files"])


def format() -> None:  # pylint: disable=redefined-builtin
    check_call(["black", "."])
    check_call(["isort", "."])
    check_call(
        [
            "autoflake",
            "--in-place",
            "--recursive",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--ignore-init-module-imports",
            ".",
        ]
    )


def lint() -> None:
    check_call(["flake8", "src", "tests"])
    check_call(["pylint", "src", "tests"])
    check_call(["mypy", "src", "tests"])
    check_call(["bandit", "-r", "src"])


def test() -> None:
    check_call(["pytest"])


def test_cov_term() -> None:
    check_call(["pytest", "--cov=src", "--cov-branch", "--cov-report=term-missing"])


def test_cov_html() -> None:
    check_call(["pytest", "--cov=src", "--cov-branch", "--cov-report=html:test_results/htmlcov"])


def test_ci() -> None:
    check_call(
        [
            "pytest",
            "--cov=src",
            "--cov-branch",
            "--cov-report=xml:test_results/coverage.xml",
            "--cov-report=html:test_results/htmlcov",
            "--junitxml=test_results/tests.xml",
        ]
    )

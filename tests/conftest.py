import pytest
from pytest import MonkeyPatch


@pytest.fixture(name="set_envvars_for_testing", scope="session")
def set_envvars_for_testing_fixture(monkeypatch_session: MonkeyPatch) -> None:
    monkeypatch_session.setenv("ENV", "testing")
    monkeypatch_session.setenv("DEBUG", "false")
    monkeypatch_session.setenv("TESTING", "true")
    monkeypatch_session.setenv("SQLALCHEMY_DATABASE_URI", "sqlite://")

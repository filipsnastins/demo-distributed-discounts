import pytest
from flask import Flask
from pytest import MonkeyPatch

from app import create_app, db


@pytest.fixture(name="set_envvars_for_testing", autouse=True)
def set_envvars_for_testing_fixture(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("ENV", "testing")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("SQLALCHEMY_DATABASE_URI", "sqlite://")


@pytest.fixture(name="app")
def app_fixture() -> Flask:
    app = create_app()
    with app.app_context():
        db.create_all()

    return app


@pytest.fixture
def client(app):
    return app.test_client()

from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url

from app.config import settings
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def test_database() -> Generator[None, None, None]:
    """Create the dedicated test database, and refuse to run anywhere else."""
    url = make_url(settings.database_url)
    database = url.database or ""
    if not database.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run tests against database {database!r}: the name must end "
            "with '_test' so the development data is never touched. Set DATABASE_URL."
        )

    # Demo seeding would make row-count assertions depend on startup behaviour.
    settings.seed_demo_data = False

    # The configured role is the Postgres superuser in compose, so it can create.
    admin_engine = create_engine(
        url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin_engine.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database}
        )
        if exists is None:
            connection.execute(text(f'CREATE DATABASE "{database}"'))
    admin_engine.dispose()
    yield


@pytest.fixture(scope="session")
def engine(test_database: None) -> Generator[Engine, None, None]:
    """Direct engine access for arranging data and asserting stored rows."""
    test_engine = create_engine(settings.database_url, pool_pre_ping=True)
    yield test_engine
    test_engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(engine: Engine) -> Generator[None, None, None]:
    yield
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE tickets"))


@pytest.fixture()
def client(test_database: None) -> Generator[TestClient, None, None]:
    # Entering the context manager runs the app lifespan, which creates tables.
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def make_ticket(client: TestClient) -> Callable[..., dict]:
    """Create a ticket through the API and return the response body."""

    def _make_ticket(**overrides: object) -> dict:
        payload = {
            "title": "Test ticket",
            "description": "Something is broken.",
            "priority": "medium",
            "tags": [],
        } | overrides
        response = client.post("/api/v1/tickets", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make_ticket

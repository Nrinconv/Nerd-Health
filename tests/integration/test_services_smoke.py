"""Both services must answer. These tests fail, never skip, when they are down."""

from __future__ import annotations

import httpx
import psycopg
import pytest

from nerdhealth.config import Settings

HINT = "Start the services first: `docker compose up -d --wait` (or `make up`)."


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None)


def test_qdrant_answers(settings: Settings) -> None:
    try:
        response = httpx.get(f"{settings.qdrant_url}/readyz", timeout=5)
    except httpx.HTTPError as exc:
        pytest.fail(f"Qdrant is not reachable at {settings.qdrant_url}: {exc}. {HINT}")
    assert response.status_code == 200, f"Qdrant is not ready. {HINT}"


def test_postgres_answers(settings: Settings) -> None:
    try:
        with psycopg.connect(settings.database_url, connect_timeout=5) as conn:
            row = conn.execute("SELECT 1").fetchone()
    except psycopg.OperationalError as exc:
        pytest.fail(f"Postgres is not reachable at {settings.database_url}: {exc}. {HINT}")
    assert row == (1,)

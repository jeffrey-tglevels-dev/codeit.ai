# Generated from the Contract. Do not edit.
"""Shared setup: a test client on a temporary SQLite database, emptied before every test."""

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

_DB_DIR = tempfile.mkdtemp(prefix="app-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_DB_DIR) / 'test.db'}"

from app.core.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_db() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c

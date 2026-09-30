import os

# Set before importing backend.app.main, so the module-level engine it
# creates (used once for the initial create_all()) never touches the real
# dev database file.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
# The rate limiter's in-memory buckets are keyed by the FastAPI app
# instance, which conftest imports once and reuses across every test in
# the session (not per-test) — so without this, tests would trip each
# other's rate limits well before hitting any real bug.
os.environ.setdefault("RATE_LIMITING_ENABLED", "false")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.app.models  # noqa: F401
from backend.app.database.base import Base
from backend.app.database.session import get_db
from backend.app.main import app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "supersecret123", "full_name": "Test User"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "supersecret123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

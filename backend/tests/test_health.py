from __future__ import annotations

from app.main import app
from fastapi.testclient import TestClient

# Plain TestClient (not the context manager) skips lifespan, so the health
# check runs without touching the database or external services.
client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

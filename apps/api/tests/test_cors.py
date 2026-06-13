"""Tests for local frontend CORS access."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_local_frontend_preflight_is_allowed() -> None:
    response = client.options(
        "/simulate",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_unlisted_origin_is_not_allowed() -> None:
    response = client.options(
        "/simulate",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert "access-control-allow-origin" not in response.headers

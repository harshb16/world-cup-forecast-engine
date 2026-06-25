"""Diagnostic simulation endpoint limits."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_simulate_endpoint_caps_diagnostic_requests() -> None:
    response = client.post(
        "/simulate",
        json={"n_simulations": 2000, "model_type": "calibrated_elo"},
    )
    assert response.status_code == 422

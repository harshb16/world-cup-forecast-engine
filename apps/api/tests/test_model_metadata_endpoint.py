"""Tests for public model metadata."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_models_endpoint_returns_current_baselines() -> None:
    response = client.get("/models")

    assert response.status_code == 200
    models = response.json()
    model_ids = {model["id"] for model in models}

    assert model_ids == {"elo", "poisson", "calibrated_elo"}
    assert all(model["is_ml"] is False for model in models)
    assert all(model["assumptions"] for model in models)
    assert all(model["limitations"] for model in models)


def test_models_endpoint_does_not_claim_ml_exists() -> None:
    response = client.get("/models")

    assert response.status_code == 200
    combined_text = " ".join(
        " ".join(model["limitations"] + model["assumptions"])
        for model in response.json()
    ).lower()

    assert "not trained" in combined_text or "not calibrated" in combined_text
    assert "machine-learning" in combined_text or "learn from historical" in combined_text

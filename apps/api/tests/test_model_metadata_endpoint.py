"""Tests for public model metadata."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_models_endpoint_returns_current_baselines() -> None:
    response = client.get("/models")

    assert response.status_code == 200
    models = response.json()
    model_ids = {model["id"] for model in models}

    assert model_ids == {
        "elo",
        "poisson",
        "calibrated_elo",
        "dixon_coles",
        "oracle_v2",
        "gbm",
        "oracle_v3",
    }
    assert any(model["is_ml"] for model in models)
    assert next(model for model in models if model["id"] == "calibrated_elo")[
        "maturity"
    ] == "production"
    assert all(
        model["maturity"] == "experimental"
        for model in models
        if model["id"] in {"oracle_v2", "gbm", "oracle_v3"}
    )
    assert all(model["is_ml"] is False for model in models if model["id"] in {"elo", "poisson", "calibrated_elo", "dixon_coles", "oracle_v2"})
    assert all(model["assumptions"] for model in models)
    assert all(model["limitations"] for model in models)


def test_models_endpoint_describes_experimental_models_honestly() -> None:
    response = client.get("/models")

    assert response.status_code == 200
    combined_text = " ".join(
        " ".join(model["limitations"] + model["assumptions"])
        for model in response.json()
    ).lower()

    assert "holdout gain" in combined_text
    assert "synthetic labels" in combined_text
    assert "oracle v2" in " ".join(model["name"].lower() for model in response.json())
    assert "oracle v3" in " ".join(model["name"].lower() for model in response.json())

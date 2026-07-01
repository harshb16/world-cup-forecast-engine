"""Tests for historical tournament backtesting."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.backtest_service import calculate_historical_backtest

client = TestClient(app)


def test_historical_backtest_endpoint_returns_2022_metrics() -> None:
    response = client.get("/evaluation/historical?tournament=2022&model_type=poisson")

    assert response.status_code == 200
    payload = response.json()

    assert payload["tournament"] == "2022"
    assert payload["model_type"] == "poisson"
    assert payload["sample_size"] == 24
    assert payload["accuracy"] is not None
    assert payload["brier_score"] is not None
    assert payload["log_loss"] is not None
    assert len(payload["calibration_bins"]) == 10
    assert len(payload["per_match_details"]) == 24
    assert any("out-of-sample" in item.lower() for item in payload["limitations"])


def test_historical_backtest_rejects_unsupported_tournament() -> None:
    response = client.get("/evaluation/historical?tournament=2018")

    assert response.status_code == 422


def test_historical_backtest_scores_are_deterministic() -> None:
    first = calculate_historical_backtest("2022", "elo")
    second = calculate_historical_backtest("2022", "elo")

    assert first.sample_size == 24
    assert first.accuracy == pytest.approx(second.accuracy)
    assert first.brier_score == pytest.approx(second.brier_score)
    assert first.log_loss == pytest.approx(second.log_loss)

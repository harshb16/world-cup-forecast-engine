"""Tests for baseline backtesting endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.backtesting import calculate_backtesting_metrics


client = TestClient(app)


def test_backtesting_endpoint_returns_processed_metrics() -> None:
    response = client.get("/backtesting?model_type=poisson")

    assert response.status_code == 200
    metrics = response.json()

    assert metrics["model_type"] == "poisson"
    assert metrics["data_mode"] == "processed"
    assert metrics["sample_size"] == 4
    assert metrics["accuracy"] is not None
    assert metrics["brier_score"] is not None
    assert metrics["log_loss"] is not None
    assert metrics["limitations"]


def test_backtesting_metrics_are_deterministic() -> None:
    first = calculate_backtesting_metrics("elo", "processed")
    second = calculate_backtesting_metrics("elo", "processed")

    assert first.sample_size == 4
    assert first.accuracy == pytest.approx(second.accuracy)
    assert first.brier_score == pytest.approx(second.brier_score)
    assert first.log_loss == pytest.approx(second.log_loss)


def test_backtesting_sample_mode_handles_no_completed_results() -> None:
    metrics = calculate_backtesting_metrics("poisson", "sample")

    assert metrics.sample_size == 0
    assert metrics.accuracy is None
    assert metrics.brier_score is None
    assert metrics.log_loss is None

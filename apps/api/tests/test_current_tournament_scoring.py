"""Tests for current-tournament scoring."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.current_tournament_scoring import (
    calculate_current_tournament_scores,
)


client = TestClient(app)


def test_current_scoring_endpoint_returns_processed_metrics() -> None:
    response = client.get("/evaluation/current?model_type=poisson")

    assert response.status_code == 200
    metrics = response.json()

    assert metrics["model_type"] == "poisson"
    assert metrics["data_mode"] == "processed"
    assert metrics["sample_size"] >= 4
    assert metrics["accuracy"] is not None
    assert metrics["brier_score"] is not None
    assert metrics["log_loss"] is not None
    assert metrics["limitations"]


def test_current_scoring_endpoint_supports_calibrated_elo() -> None:
    response = client.get("/evaluation/current?model_type=calibrated_elo")

    assert response.status_code == 200
    assert response.json()["model_type"] == "calibrated_elo"


def test_current_scoring_endpoint_supports_oracle_v2() -> None:
    response = client.get("/evaluation/current?model_type=oracle_v2")

    assert response.status_code == 200
    assert response.json()["model_type"] == "oracle_v2"


def test_current_scoring_endpoint_defaults_to_calibrated_elo() -> None:
    response = client.get("/evaluation/current")

    assert response.status_code == 200
    assert response.json()["model_type"] == "calibrated_elo"


def test_current_tournament_scores_are_deterministic() -> None:
    first = calculate_current_tournament_scores("elo", "processed")
    second = calculate_current_tournament_scores("elo", "processed")

    assert first.sample_size >= 4
    assert first.accuracy == pytest.approx(second.accuracy)
    assert first.brier_score == pytest.approx(second.brier_score)
    assert first.log_loss == pytest.approx(second.log_loss)


def test_current_scoring_endpoint_returns_calibration_bins() -> None:
    response = client.get("/evaluation/current?model_type=oracle_v2")

    assert response.status_code == 200
    metrics = response.json()
    assert len(metrics["calibration_bins"]) == 10
    assert metrics["per_match_details"]


def test_current_scoring_sample_mode_handles_no_completed_results() -> None:
    metrics = calculate_current_tournament_scores("poisson", "sample")

    assert metrics.sample_size == 0
    assert metrics.accuracy is None
    assert metrics.brier_score is None
    assert metrics.log_loss is None


def test_knockout_penalty_match_scores_as_regulation_draw() -> None:
    from app.models.domain import MatchResult
    from app.services.current_tournament_scoring import _actual_outcome

    result = MatchResult(
        team_a_goals=1,
        team_b_goals=1,
        played=True,
        decided_by_penalties=True,
        penalty_team_a_goals=4,
        penalty_team_b_goals=3,
    )

    assert _actual_outcome(result, "TEAM_A") == "draw"


def test_legacy_backtesting_endpoint_is_not_exposed() -> None:
    response = client.get("/backtesting")

    assert response.status_code == 404

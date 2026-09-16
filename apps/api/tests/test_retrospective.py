"""Tests for tournament retrospective endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.retrospective_service import calculate_retrospective


client = TestClient(app)


def test_retrospective_endpoint_returns_arc_and_scoring() -> None:
    response = client.get("/retrospective?model_type=poisson")

    assert response.status_code == 200
    payload = response.json()

    assert payload["model_type"] == "poisson"
    assert payload["data_mode"] == "processed"
    assert payload["champion_arc"]
    assert payload["scoring"]["sample_size"] >= 4
    assert len(payload["scoring"]["calibration_bins"]) == 10
    assert payload["limitations"]


def test_retrospective_is_deterministic() -> None:
    first = calculate_retrospective("elo", "processed")
    second = calculate_retrospective("elo", "processed")

    assert first.model_type == second.model_type
    assert first.champion_arc == second.champion_arc
    assert first.top_hits == second.top_hits
    assert first.top_misses == second.top_misses
    assert first.scoring.accuracy == pytest.approx(second.scoring.accuracy)


def test_retrospective_hits_and_misses_are_ranked() -> None:
    payload = calculate_retrospective("oracle_v2", "processed")

    if payload.top_hits:
        confidences = [item.confidence for item in payload.top_hits]
        assert confidences == sorted(confidences, reverse=True)
        assert all(item.correct for item in payload.top_hits)

    if payload.top_misses:
        confidences = [item.confidence for item in payload.top_misses]
        assert confidences == sorted(confidences, reverse=True)
        assert all(not item.correct for item in payload.top_misses)

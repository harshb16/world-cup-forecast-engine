"""Tests for probability snapshot append logic and the /analytics/probability-history endpoint."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mock_simulation_result(champion_probs: dict[str, float]) -> MagicMock:
    result = MagicMock()
    result.champion_probabilities = champion_probs
    return result


def test_append_probability_snapshot_creates_file(tmp_path: Path) -> None:
    """_append_probability_snapshot writes a new file when none exists."""
    import app.services.data_sync_service as dss

    champion_probs = {"ARGENTINA": 0.22, "FRANCE": 0.18}

    with patch.object(dss, "PROCESSED_DIR", tmp_path):
        with patch(
            "app.services.simulation_service.run_simulation",
            return_value=_mock_simulation_result(champion_probs),
        ):
            dss._append_probability_snapshot("2026-06-18T00:00:00+00:00")

    history_path = tmp_path / "probability_history.json"
    assert history_path.exists()
    data = json.loads(history_path.read_text())
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["timestamp"] == "2026-06-18T00:00:00+00:00"
    assert data[0]["champion_probabilities"] == champion_probs


def test_append_probability_snapshot_grows_array(tmp_path: Path) -> None:
    """_append_probability_snapshot appends to an existing file."""
    import app.services.data_sync_service as dss

    history_path = tmp_path / "probability_history.json"
    initial: list[dict] = [
        {
            "timestamp": "2026-06-17T00:00:00+00:00",
            "champion_probabilities": {"ARGENTINA": 0.20},
        }
    ]
    history_path.write_text(json.dumps(initial))

    champion_probs = {"ARGENTINA": 0.25, "FRANCE": 0.15}

    with patch.object(dss, "PROCESSED_DIR", tmp_path):
        with patch(
            "app.services.simulation_service.run_simulation",
            return_value=_mock_simulation_result(champion_probs),
        ):
            dss._append_probability_snapshot("2026-06-18T00:00:00+00:00")

    data = json.loads(history_path.read_text())
    assert len(data) == 2
    assert data[1]["timestamp"] == "2026-06-18T00:00:00+00:00"
    assert data[1]["champion_probabilities"] == champion_probs


def test_current_matchday_uses_official_schedule() -> None:
    import app.services.data_sync_service as dss

    with patch.object(dss, "group_matchday_for_date", return_value=3):
        assert dss._current_matchday() == 3


def test_append_probability_snapshot_silences_errors(tmp_path: Path) -> None:
    """_append_probability_snapshot does not raise if simulation fails."""
    import app.services.data_sync_service as dss

    with patch.object(dss, "PROCESSED_DIR", tmp_path):
        with patch(
            "app.services.simulation_service.run_simulation",
            side_effect=RuntimeError("boom"),
        ):
            dss._append_probability_snapshot("2026-06-18T00:00:00+00:00")

    history_path = tmp_path / "probability_history.json"
    assert not history_path.exists()


def test_probability_history_endpoint_empty(tmp_path: Path) -> None:
    """GET /analytics/probability-history returns empty list when no history file exists."""
    import app.services.data_sync_service as dss

    with patch.object(dss, "PROCESSED_DIR", tmp_path):
        response = client.get("/analytics/probability-history")

    assert response.status_code == 200
    body = response.json()
    assert body["snapshots"] == []


def test_probability_history_endpoint_returns_data(tmp_path: Path) -> None:
    """GET /analytics/probability-history returns stored snapshots."""
    import app.services.data_sync_service as dss
    import app.api.routes as routes_module

    history: list[dict] = [
        {
            "timestamp": "2026-06-17T00:00:00+00:00",
            "champion_probabilities": {"ARGENTINA": 0.20, "FRANCE": 0.15},
        },
        {
            "timestamp": "2026-06-18T00:00:00+00:00",
            "champion_probabilities": {"ARGENTINA": 0.25, "FRANCE": 0.14},
        },
    ]
    history_path = tmp_path / "probability_history.json"
    history_path.write_text(json.dumps(history))

    with patch.object(dss, "PROCESSED_DIR", tmp_path):
        # Force routes module to see the same module instance
        import sys
        sys.modules["app.services.data_sync_service"] = dss
        response = client.get("/analytics/probability-history")

    assert response.status_code == 200
    body = response.json()
    assert len(body["snapshots"]) == 2
    assert body["snapshots"][0]["timestamp"] == "2026-06-17T00:00:00+00:00"
    assert body["snapshots"][1]["champion_probabilities"]["ARGENTINA"] == pytest.approx(0.25)

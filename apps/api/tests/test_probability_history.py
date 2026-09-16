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

    with patch("app.services.data_sync_service.get_processed_data_dir", return_value=tmp_path):
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

    with patch("app.services.data_sync_service.get_processed_data_dir", return_value=tmp_path):
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

    with patch("app.services.data_sync_service.get_processed_data_dir", return_value=tmp_path):
        with patch(
            "app.services.simulation_service.run_simulation",
            side_effect=RuntimeError("boom"),
        ):
            dss._append_probability_snapshot("2026-06-18T00:00:00+00:00")

    history_path = tmp_path / "probability_history.json"
    assert not history_path.exists()


def test_probability_history_endpoint_returns_milestone_snapshots() -> None:
    """GET /analytics/probability-history returns match-progress milestones."""
    response = client.get("/analytics/probability-history?n_simulations=20&model_type=elo")

    assert response.status_code == 200
    body = response.json()
    snapshots = body["snapshots"]
    assert len(snapshots) >= 1
    assert snapshots[0]["label"] == "Before Matchday 1"
    assert snapshots[0]["milestone_id"] == "before_group_md1"
    assert snapshots[0]["champion_probabilities"]


def test_build_probability_timeline_is_deterministic() -> None:
    from app.services.probability_timeline_service import build_probability_timeline

    first = build_probability_timeline("processed", model_type="elo", n_simulations=25, seed=7)
    second = build_probability_timeline("processed", model_type="elo", n_simulations=25, seed=7)

    assert first == second


def test_tournament_at_milestone_keeps_only_matchday_one_results() -> None:
    from app.models.domain import Group, Match, MatchResult, Team, TournamentConfig
    from app.services.probability_timeline_service import _Milestone, _tournament_at_milestone

    teams = [
        Team(id="T1", name="T1", group_id="A", rating=1500),
        Team(id="T2", name="T2", group_id="A", rating=1500),
        Team(id="T3", name="T3", group_id="A", rating=1500),
        Team(id="T4", name="T4", group_id="A", rating=1500),
    ]
    config = TournamentConfig(
        teams=teams,
        groups=[Group(id="A", name="Group A", team_ids=["T1", "T2", "T3", "T4"])],
        matches=[
            Match(
                id="A1",
                stage="group",
                group_id="A",
                team_a_id="T1",
                team_b_id="T2",
                result=MatchResult(team_a_goals=1, team_b_goals=0, played=True),
            ),
            Match(
                id="A2",
                stage="group",
                group_id="A",
                team_a_id="T3",
                team_b_id="T4",
                result=MatchResult(team_a_goals=2, team_b_goals=2, played=True),
            ),
        ],
    )
    raw_fixtures = {
        "A1": {"kickoff_utc": "2026-06-11T19:00:00Z"},
        "A2": {"kickoff_utc": "2026-06-19T01:00:00Z"},
    }
    sliced = _tournament_at_milestone(
        config,
        raw_fixtures,
        _Milestone("after_group_md1", "After Matchday 1", 1),
    )

    by_id = {match.id: match for match in sliced.matches}
    assert by_id["A1"].result is not None and by_id["A1"].result.played
    assert by_id["A2"].result is None


def test_build_probability_timeline_skips_unchanged_milestones() -> None:
    from app.models.domain import SimulationSummary
    from app.services.probability_timeline_service import build_probability_timeline

    summary = SimulationSummary(
        stage_probabilities={
            "ARGENTINA": {
                "group_stage_exit": 0.0,
                "round_of_32": 0.0,
                "round_of_16": 0.0,
                "quarter_final": 0.0,
                "semi_final": 0.0,
                "final": 0.0,
                "champion": 0.2,
            }
        },
    )

    with patch(
        "app.services.probability_timeline_service.run_simulations",
        return_value=summary,
    ):
        response = build_probability_timeline("processed", model_type="elo", n_simulations=10, seed=1)

    labels = [snapshot.label for snapshot in response.snapshots]
    assert labels[0] == "Before Matchday 1"
    assert labels.count("Before Matchday 1") == 1

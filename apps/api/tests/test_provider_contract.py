"""Provider contract tests for result synchronization."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services import results_sync_service
from app.services.provider_status import fifa_status, football_data_status


def test_football_data_status_maps_live_states() -> None:
    assert football_data_status("IN_PLAY") == "in_play"
    assert football_data_status("PAUSED") == "in_play"
    assert football_data_status("FINISHED") == "finished"
    assert football_data_status("TIMED") == "scheduled"


def test_fifa_status_maps_live_states() -> None:
    assert fifa_status(1) == "in_play"
    assert fifa_status(2) == "in_play"
    assert fifa_status(0) == "finished"
    assert fifa_status(4) == "scheduled"


def test_fetch_provider_matches_falls_back_to_fifa_on_timeout(monkeypatch) -> None:
    monkeypatch.setenv("FOOTBALL_DATA_API_TOKEN", "token")
    fifa_payload = {"Results": [{"Home": {"Abbreviation": "MEX"}, "Away": {"Abbreviation": "RSA"}}]}

    with patch.object(
        results_sync_service,
        "_fetch_json",
        side_effect=[TimeoutError("delay"), fifa_payload],
    ):
        provider, matches = results_sync_service._fetch_provider_matches()

    assert provider == "FIFA API fallback"
    assert matches == fifa_payload["Results"]


def test_fetch_provider_matches_prefers_football_data_when_configured(
    monkeypatch,
) -> None:
    monkeypatch.setenv("FOOTBALL_DATA_API_TOKEN", "token")
    payload = {"matches": [{"status": "FINISHED"}]}

    with patch.object(results_sync_service, "_fetch_json", return_value=payload):
        provider, matches = results_sync_service._fetch_provider_matches()

    assert provider == "football-data.org"
    assert matches == payload["matches"]


def test_in_play_update_sets_status_without_publishing_result() -> None:
    fixture = {
        "id": "A2",
        "stage": "group",
        "team_a_id": "KOR",
        "team_b_id": "CZECHIA",
        "status": "scheduled",
        "result": None,
        "winner_team_id": None,
    }
    incoming = {
        "status": "in_play",
        "team_a_goals": 1,
        "team_b_goals": 0,
        "kickoff_utc": "2026-06-12T19:00:00Z",
    }

    updated = results_sync_service._apply_match_update(
        fixture,
        incoming,
        "football-data.org",
    )

    assert updated["status"] == "in_play"
    assert updated["result"] == {
        "played": False,
        "team_a_goals": 1,
        "team_b_goals": 0,
    }

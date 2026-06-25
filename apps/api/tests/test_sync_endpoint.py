"""Tests for protected, atomic match-result synchronization."""

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import SyncResponse
from app.services import results_sync_service


client = TestClient(app)


def test_legacy_sync_endpoint_is_not_public() -> None:
    response = client.post("/sync")

    assert response.status_code == 404


def test_admin_sync_requires_configuration(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WCO_ADMIN_SYNC_KEY", raising=False)

    response = client.post("/admin/sync/results")

    assert response.status_code == 503


def test_admin_sync_rejects_invalid_key(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "correct-key")

    response = client.post(
        "/admin/sync/results",
        headers={"X-WCO-Admin-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_admin_sync_runs_with_valid_key(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "correct-key")
    expected = SyncResponse(
        success=True,
        last_updated="2026-06-25T12:00:00+00:00",
        provider="football-data.org",
        completed_result_count=54,
        changed_fixture_count=0,
    )

    with patch("app.api.routes.sync_results", return_value=expected):
        response = client.post(
            "/admin/sync/results",
            headers={"X-WCO-Admin-Key": "correct-key"},
        )

    assert response.status_code == 200
    assert response.json()["provider"] == "football-data.org"


def test_football_data_result_is_oriented_to_fixture_order() -> None:
    fixtures = [
        {
            "id": "A1",
            "stage": "group",
            "team_a_id": "MEXICO",
            "team_b_id": "RSA",
            "kickoff": "2026-06-11",
            "kickoff_utc": "2026-06-11T19:00:00Z",
            "status": "scheduled",
            "result": None,
            "winner_team_id": None,
        }
    ]
    teams = [
        {"id": "MEXICO", "name": "Mexico"},
        {"id": "RSA", "name": "South Africa"},
    ]
    provider_matches = [
        {
            "status": "FINISHED",
            "utcDate": "2026-06-11T19:00:00Z",
            "homeTeam": {"name": "South Africa", "tla": "RSA"},
            "awayTeam": {"name": "Mexico", "tla": "MEX"},
            "score": {"fullTime": {"home": 0, "away": 2}},
        }
    ]

    updated, results, changed = results_sync_service._merge_provider_matches(
        fixtures,
        teams,
        [],
        "football-data.org",
        provider_matches,
    )

    assert changed == 1
    assert updated[0]["result"] == {
        "played": True,
        "team_a_goals": 2,
        "team_b_goals": 0,
    }
    assert results[0]["team_a_goals"] == 2
    assert results[0]["team_b_goals"] == 0


def test_provider_score_conflict_is_rejected() -> None:
    fixtures = [
        {
            "id": "A1",
            "stage": "group",
            "team_a_id": "MEXICO",
            "team_b_id": "RSA",
            "kickoff": "2026-06-11",
            "kickoff_utc": "2026-06-11T19:00:00Z",
            "status": "finished",
            "result": {
                "played": True,
                "team_a_goals": 2,
                "team_b_goals": 0,
            },
            "winner_team_id": "MEXICO",
        }
    ]
    teams = [
        {"id": "MEXICO", "name": "Mexico"},
        {"id": "RSA", "name": "South Africa"},
    ]
    provider_matches = [
        {
            "status": "FINISHED",
            "utcDate": "2026-06-11T19:00:00Z",
            "homeTeam": {"name": "Mexico", "tla": "MEX"},
            "awayTeam": {"name": "South Africa", "tla": "RSA"},
            "score": {"fullTime": {"home": 1, "away": 0}},
        }
    ]

    with pytest.raises(results_sync_service.ResultsConflictError):
        results_sync_service._merge_provider_matches(
            fixtures,
            teams,
            [],
            "football-data.org",
            provider_matches,
        )


def test_failed_validation_does_not_publish_partial_files(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    processed_dir = tmp_path / "processed"
    shutil.copytree(results_sync_service.PROCESSED_DIR, processed_dir)
    monkeypatch.setattr(results_sync_service, "PROCESSED_DIR", processed_dir)
    originals = {
        filename: (processed_dir / filename).read_bytes()
        for filename in results_sync_service.SYNC_FILES
    }

    with (
        patch(
            "app.services.results_sync_service._fetch_provider_matches",
            return_value=(
                "FIFA API fallback",
                [
                    {
                        "Home": {"Abbreviation": "MEX"},
                        "Away": {"Abbreviation": "RSA"},
                        "MatchStatus": 0,
                        "HomeTeamScore": 2,
                        "AwayTeamScore": 0,
                        "KickOffTimeUtc": "2026-06-11T19:00:00Z",
                    }
                ],
            ),
        ),
        patch(
            "app.services.results_sync_service._validate_staged_data",
            return_value=["fixture validation failed"],
        ),
        patch("app.services.results_sync_service._append_probability_snapshot"),
    ):
        response = results_sync_service.sync_results()

    assert response.success is False
    assert "fixture validation failed" in response.errors[0]
    assert {
        filename: (processed_dir / filename).read_bytes()
        for filename in results_sync_service.SYNC_FILES
    } == originals


def test_successful_sync_publishes_consistent_snapshot(
    tmp_path: Path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    processed_dir = tmp_path / "processed"
    shutil.copytree(results_sync_service.PROCESSED_DIR, processed_dir)
    monkeypatch.setattr(results_sync_service, "PROCESSED_DIR", processed_dir)
    fixtures = json.loads((processed_dir / "fixtures.json").read_text())
    known = fixtures[0]
    provider_match = {
        "Home": {"Abbreviation": "MEX"},
        "Away": {"Abbreviation": "RSA"},
        "MatchStatus": 0,
        "HomeTeamScore": known["result"]["team_a_goals"],
        "AwayTeamScore": known["result"]["team_b_goals"],
        "KickOffTimeUtc": known["kickoff_utc"],
    }

    with (
        patch(
            "app.services.results_sync_service._fetch_provider_matches",
            return_value=("FIFA API fallback", [provider_match]),
        ),
        patch("app.services.results_sync_service._append_probability_snapshot"),
    ):
        response = results_sync_service.sync_results()

    metadata = json.loads((processed_dir / "metadata.json").read_text())
    quality = json.loads((processed_dir / "data_quality.json").read_text())
    results = json.loads((processed_dir / "results.json").read_text())
    assert response.success is True
    assert metadata["last_updated"] == quality["last_refresh"]
    assert metadata["result_source"] == "FIFA API fallback"
    assert quality["source_coverage"]["completed_results"] == len(results)

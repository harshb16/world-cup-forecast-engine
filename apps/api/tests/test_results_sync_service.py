"""Service-level tests for atomic result synchronization."""

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from app.services import results_sync_service
from app.services.runtime_store import (
    BOOTSTRAP_PROCESSED_DIR,
    get_active_data_directory,
    publish_data_snapshot,
    reset_runtime_store_for_tests,
)


@pytest.fixture
def runtime_processed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    runtime_root = tmp_path / "runtime"
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(runtime_root))
    reset_runtime_store_for_tests()
    staged = tmp_path / "bootstrap"
    shutil.copytree(BOOTSTRAP_PROCESSED_DIR, staged)
    publish_data_snapshot(staged)
    active = get_active_data_directory()
    assert active is not None
    return active


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
    runtime_processed: Path,
) -> None:
    originals = {
        filename: (runtime_processed / filename).read_bytes()
        for filename in results_sync_service.SYNC_FILES
    }
    active_before = runtime_processed

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
    assert get_active_data_directory() == active_before
    assert {
        filename: (runtime_processed / filename).read_bytes()
        for filename in results_sync_service.SYNC_FILES
    } == originals


def test_knockout_penalty_result_sets_winner() -> None:
    fixtures = [
        {
            "id": "R32-01",
            "stage": "Round of 32",
            "team_a_id": "MEXICO",
            "team_b_id": "RSA",
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
            "utcDate": "2026-06-28T19:00:00Z",
            "homeTeam": {"name": "Mexico", "tla": "MEX"},
            "awayTeam": {"name": "South Africa", "tla": "RSA"},
            "score": {
                "fullTime": {"home": 1, "away": 1},
                "extraTime": {"home": 1, "away": 1},
                "penalties": {"home": 4, "away": 3},
            },
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
    assert updated[0]["result"]["decided_by_penalties"] is True
    assert updated[0]["result"]["penalty_team_a_goals"] == 4
    assert updated[0]["winner_team_id"] == "MEXICO"
    assert results[0]["stage"] == "Round of 32"


def test_knockout_progression_guard_rejects_invalid_team() -> None:
    fixtures = [
        {
            "id": "R32-01",
            "stage": "Round of 32",
            "team_a_id": "MEXICO",
            "team_b_id": "RSA",
            "status": "finished",
            "result": {"played": True, "team_a_goals": 2, "team_b_goals": 0},
            "winner_team_id": "MEXICO",
        },
        {
            "id": "R16-01",
            "stage": "Round of 16",
            "team_a_id": "MEXICO",
            "team_b_id": "BRAZIL",
            "status": "scheduled",
            "result": None,
            "winner_team_id": None,
        },
    ]
    teams = [
        {"id": "MEXICO", "name": "Mexico"},
        {"id": "RSA", "name": "South Africa"},
        {"id": "BRAZIL", "name": "Brazil"},
    ]
    provider_matches = [
        {
            "status": "FINISHED",
            "homeTeam": {"name": "Mexico", "tla": "MEX"},
            "awayTeam": {"name": "Brazil", "tla": "BRA"},
            "score": {"fullTime": {"home": 1, "away": 0}},
        }
    ]

    with pytest.raises(results_sync_service.ResultsSyncError):
        results_sync_service._merge_provider_matches(
            fixtures,
            teams,
            [],
            "football-data.org",
            provider_matches,
        )


def test_materialize_next_knockout_round_from_completed_r32() -> None:
    from app.models.domain import MatchResult, TournamentConfig
    from app.services.bracket_materialization_service import (
        build_next_knockout_round,
        is_knockout_round_complete,
        materialize_round_of_32_if_ready,
    )
    from app.services.data_loader import load_tournament

    config = load_tournament("sample")
    completed_matches = [
        match.model_copy(
            update={
                "result": MatchResult(team_a_goals=2, team_b_goals=1, played=True),
                "winner_team_id": match.team_a_id,
            }
        )
        for match in config.matches
        if match.stage == "group"
    ]
    config = config.model_copy(update={"matches": completed_matches})
    r32 = materialize_round_of_32_if_ready(config)
    config = config.model_copy(update={"matches": [*config.matches, *r32]})
    completed_r32 = [
        match.model_copy(
            update={
                "result": MatchResult(team_a_goals=1, team_b_goals=0, played=True),
                "winner_team_id": match.team_a_id,
            }
        )
        for match in r32
    ]
    group_matches = [match for match in config.matches if match.stage == "group"]
    config = config.model_copy(update={"matches": [*group_matches, *completed_r32]})
    assert is_knockout_round_complete(config, "Round of 32")
    r16 = build_next_knockout_round(config, "Round of 32", "Round of 16")
    assert len(r16) == 8
    assert all(match.stage == "Round of 16" for match in r16)


def test_successful_sync_publishes_consistent_snapshot(
    runtime_processed: Path,
) -> None:
    fixtures = json.loads((runtime_processed / "fixtures.json").read_text())
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
        patch("app.services.results_sync_service._refresh_forecast_snapshot"),
    ):
        response = results_sync_service.sync_results()

    active_dir = get_active_data_directory()
    assert active_dir is not None
    metadata = json.loads((active_dir / "metadata.json").read_text())
    quality = json.loads((active_dir / "data_quality.json").read_text())
    results = json.loads((active_dir / "results.json").read_text())
    assert response.success is True
    assert metadata["last_updated"] == quality["last_refresh"]
    assert metadata["result_source"] == "FIFA API fallback"
    assert quality["source_coverage"]["completed_results"] == len(results)

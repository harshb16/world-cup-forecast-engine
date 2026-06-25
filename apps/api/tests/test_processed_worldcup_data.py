"""Tests for checked-in processed World Cup 2026 data."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
sys.path.append(str(REPO_ROOT / "scripts" / "ingest"))

from validate_processed_data import validate_processed_data  # noqa: E402


def _read(name: str):
    return json.loads((PROCESSED_DIR / name).read_text())


def test_checked_in_processed_data_is_valid() -> None:
    assert validate_processed_data(PROCESSED_DIR) == []


def test_processed_teams_include_real_world_cup_names() -> None:
    names = {team["name"] for team in _read("teams.json")}

    assert {"Argentina", "Brazil", "England", "Mexico"}.issubset(names)


def test_group_a_contains_expected_real_teams() -> None:
    teams = {team["id"]: team["name"] for team in _read("teams.json")}
    group_a = next(group for group in _read("groups.json") if group["id"] == "A")

    assert [teams[team_id] for team_id in group_a["team_ids"]] == [
        "Mexico",
        "South Africa",
        "Korea Republic",
        "Czechia",
    ]


def test_processed_fixtures_include_known_completed_results() -> None:
    fixtures = {fixture["id"]: fixture for fixture in _read("fixtures.json")}

    assert fixtures["A1"]["result"] == {
        "played": True,
        "team_a_goals": 2,
        "team_b_goals": 0,
    }
    assert fixtures["A2"]["result"] == {
        "played": True,
        "team_a_goals": 2,
        "team_b_goals": 1,
    }


def test_processed_results_include_both_team_ids() -> None:
    results = _read("results.json")

    assert results
    assert all(result.get("team_a_id") and result.get("team_b_id") for result in results)


def test_processed_quality_snapshot_matches_checked_in_results() -> None:
    metadata = _read("metadata.json")
    quality = _read("data_quality.json")
    fixtures = _read("fixtures.json")
    results = _read("results.json")
    finished_fixture_ids = {
        fixture["id"]
        for fixture in fixtures
        if fixture["status"] == "finished" and fixture["result"]["played"]
    }

    assert {result["match_id"] for result in results} == finished_fixture_ids
    assert quality["source_coverage"]["completed_results"] == len(results)
    assert quality["last_refresh"] == metadata["last_updated"]

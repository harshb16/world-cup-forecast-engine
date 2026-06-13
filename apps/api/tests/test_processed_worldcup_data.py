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

    assert fixtures["A-01"]["result"] == {
        "played": True,
        "team_a_goals": 2,
        "team_b_goals": 0,
    }
    assert fixtures["A-02"]["result"] == {
        "played": True,
        "team_a_goals": 2,
        "team_b_goals": 1,
    }

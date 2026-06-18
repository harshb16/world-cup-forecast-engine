"""Tests for FIFA World Cup ingest matching logic."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
INGEST_DIR = REPO_ROOT / "scripts" / "ingest"
SCRIPT_PATH = INGEST_DIR / "fetch_worldcup_fifa.py"


def _load_fifa_module():
    ingest_path = str(INGEST_DIR)
    if ingest_path not in sys.path:
        sys.path.insert(0, ingest_path)
    spec = importlib.util.spec_from_file_location("fetch_worldcup_fifa", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_fifa_match_index_uses_team_pairs_not_placeholder_labels() -> None:
    fifa = _load_fifa_module()
    matches = [
        {
            "PlaceHolderA": "A3",
            "Home": {"Abbreviation": "KOR"},
            "Away": {"Abbreviation": "CZE"},
            "MatchStatus": 0,
            "HomeTeamScore": 2,
            "AwayTeamScore": 1,
        }
    ]

    index = fifa.build_fifa_match_index(matches)
    assert ("CZECHIA", "KOR") in index


def test_extract_fixture_result_respects_home_away_orientation() -> None:
    fifa = _load_fifa_module()
    fixture = {
        "id": "A2",
        "team_a_id": "KOR",
        "team_b_id": "CZECHIA",
    }
    match = {
        "MatchStatus": 0,
        "Home": {"Abbreviation": "KOR"},
        "Away": {"Abbreviation": "CZE"},
        "HomeTeamScore": 2,
        "AwayTeamScore": 1,
    }

    result = fifa.extract_fixture_result(fixture, match)
    assert result == {"played": True, "team_a_goals": 2, "team_b_goals": 1}


def test_extract_fixture_result_swaps_scores_when_fixture_order_differs() -> None:
    fifa = _load_fifa_module()
    fixture = {
        "id": "A2",
        "team_a_id": "CZECHIA",
        "team_b_id": "KOR",
    }
    match = {
        "MatchStatus": 0,
        "Home": {"Abbreviation": "KOR"},
        "Away": {"Abbreviation": "CZE"},
        "HomeTeamScore": 2,
        "AwayTeamScore": 1,
    }

    result = fifa.extract_fixture_result(fixture, match)
    assert result == {"played": True, "team_a_goals": 1, "team_b_goals": 2}


def test_apply_fifa_updates_builds_results_for_finished_group_matches() -> None:
    fifa = _load_fifa_module()
    fixtures = [
        {
            "id": "A1",
            "stage": "group",
            "team_a_id": "MEXICO",
            "team_b_id": "RSA",
            "status": "scheduled",
            "result": None,
        },
        {
            "id": "A2",
            "stage": "group",
            "team_a_id": "KOR",
            "team_b_id": "CZECHIA",
            "status": "scheduled",
            "result": None,
        },
    ]
    fifa_matches = [
        {
            "PlaceHolderA": "A1",
            "Home": {"Abbreviation": "MEX"},
            "Away": {"Abbreviation": "RSA"},
            "MatchStatus": 0,
            "HomeTeamScore": 2,
            "AwayTeamScore": 0,
            "KickOffTimeUtc": "2026-06-11T19:00:00Z",
            "StadiumName": "Estadio Azteca",
        },
        {
            "PlaceHolderA": "A3",
            "Home": {"Abbreviation": "KOR"},
            "Away": {"Abbreviation": "CZE"},
            "MatchStatus": 1,
            "HomeTeamScore": None,
            "AwayTeamScore": None,
        },
    ]

    updated_fixtures, results = fifa.apply_fifa_updates(fixtures, fifa_matches)

    assert updated_fixtures[0]["status"] == "finished"
    assert updated_fixtures[0]["result"] == {
        "played": True,
        "team_a_goals": 2,
        "team_b_goals": 0,
    }
    assert updated_fixtures[0]["venue"] == "Estadio Azteca"
    assert updated_fixtures[1]["status"] == "scheduled"
    assert results == [
        {
            "match_id": "A1",
            "team_a_id": "MEXICO",
            "team_b_goals": 0,
            "team_a_goals": 2,
            "status": "finished",
            "source": fifa.RESULT_SOURCE,
        }
    ]

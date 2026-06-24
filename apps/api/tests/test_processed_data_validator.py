"""Tests for processed World Cup data validation."""

import sys
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.append(str(REPO_ROOT / "scripts" / "ingest"))

from common import write_json  # noqa: E402
from validate_processed_data import validate_processed_data  # noqa: E402


def _write_valid_dataset(base_dir: Path) -> None:
    teams = []
    groups = []
    fixtures = []
    ratings = []
    results = []

    for group_index in range(12):
        group_id = chr(ord("A") + group_index)
        team_ids = []
        for team_index in range(4):
            team_id = f"{group_id}{team_index + 1}"
            team_ids.append(team_id)
            teams.append(
                {
                    "id": team_id,
                    "name": f"Team {team_id}",
                    "group_id": group_id,
                    "rating": 1500 + group_index,
                }
            )
            ratings.append(
                {
                    "team_id": team_id,
                    "team_name": f"Team {team_id}",
                    "elo_rating": 1500 + group_index,
                    "source": "test",
                }
            )
        groups.append({"id": group_id, "name": f"Group {group_id}", "team_ids": team_ids})

        pairings = [(0, 1), (2, 3), (0, 2), (3, 1), (3, 0), (1, 2)]
        for match_index, (a_index, b_index) in enumerate(pairings, start=1):
            fixtures.append(
                {
                    "id": f"{group_id}-{match_index}",
                    "stage": "group",
                    "group_id": group_id,
                    "team_a_id": team_ids[a_index],
                    "team_b_id": team_ids[b_index],
                    "kickoff": f"2026-06-{11 + group_index:02d}",
                    "kickoff_utc": f"2026-06-{11 + group_index:02d}T19:00:00Z",
                    "venue": None,
                    "city": None,
                    "status": "scheduled",
                    "result": None,
                    "winner_team_id": None,
                }
            )

    write_json(base_dir / "teams.json", teams)
    write_json(base_dir / "groups.json", groups)
    write_json(base_dir / "fixtures.json", fixtures)
    write_json(base_dir / "results.json", results)
    write_json(base_dir / "ratings.json", ratings)
    write_json(
        base_dir / "squad_features.json",
        [
            {
                "team_id": team["id"],
                "squad_power": team["rating"],
                "coverage": 1.0,
            }
            for team in teams
        ],
    )
    write_json(
        base_dir / "model_parameters.json",
        {
            "source": {"url": "test"},
            "training_window_start": "2018-01-01",
            "team_ratings": [
                {
                    "team_id": team["id"],
                    "team_name": team["name"],
                    "source_team_name": team["name"],
                    "rating": team["rating"],
                    "fallback_used": False,
                }
                for team in teams
            ],
        },
    )
    write_json(
        base_dir / "metadata.json",
        {
            "data_mode": "processed",
            "is_real_data": True,
            "data_version": "test",
            "last_updated": "2026-06-13T00:00:00+00:00",
            "sources": [],
            "rating_source": "World Football Elo Ratings",
            "ratings_are_official": False,
            "bracket_status": "placeholder",
        },
    )


def test_validate_processed_data_accepts_valid_dataset(tmp_path: Path) -> None:
    _write_valid_dataset(tmp_path)

    assert validate_processed_data(tmp_path) == []


def test_validate_processed_data_rejects_wrong_fixture_group(tmp_path: Path) -> None:
    _write_valid_dataset(tmp_path)
    fixtures = json.loads((tmp_path / "fixtures.json").read_text())
    fixtures[0]["group_id"] = "B"
    write_json(tmp_path / "fixtures.json", fixtures)

    errors = validate_processed_data(tmp_path)

    assert any("is not in B" in error for error in errors)


def test_validate_processed_data_rejects_missing_metadata(tmp_path: Path) -> None:
    _write_valid_dataset(tmp_path)
    metadata = json.loads((tmp_path / "metadata.json").read_text())
    del metadata["rating_source"]
    write_json(tmp_path / "metadata.json", metadata)

    errors = validate_processed_data(tmp_path)

    assert "metadata missing rating_source" in errors


def test_validate_processed_data_rejects_duplicate_fixture_ids(tmp_path: Path) -> None:
    _write_valid_dataset(tmp_path)
    fixtures = json.loads((tmp_path / "fixtures.json").read_text())
    fixtures[1]["id"] = fixtures[0]["id"]
    write_json(tmp_path / "fixtures.json", fixtures)

    errors = validate_processed_data(tmp_path)

    assert "fixtures.json contains duplicate fixture ids" in errors


def test_validate_processed_data_rejects_contradictory_kickoff_dates(
    tmp_path: Path,
) -> None:
    _write_valid_dataset(tmp_path)
    fixtures = json.loads((tmp_path / "fixtures.json").read_text())
    fixtures[0]["kickoff_utc"] = "2026-06-18T19:00:00Z"
    write_json(tmp_path / "fixtures.json", fixtures)

    errors = validate_processed_data(tmp_path)

    assert "A-1 kickoff date contradicts kickoff_utc" in errors


@pytest.mark.parametrize("status", ["live", "postponed", None])
def test_validate_processed_data_rejects_unknown_fixture_status(
    tmp_path: Path,
    status: str | None,
) -> None:
    _write_valid_dataset(tmp_path)
    fixtures = json.loads((tmp_path / "fixtures.json").read_text())
    fixtures[0]["status"] = status
    write_json(tmp_path / "fixtures.json", fixtures)

    errors = validate_processed_data(tmp_path)

    assert f"A-1 has invalid status {status}" in errors


def test_validate_processed_data_rejects_scheduled_winner(tmp_path: Path) -> None:
    _write_valid_dataset(tmp_path)
    fixtures = json.loads((tmp_path / "fixtures.json").read_text())
    fixtures[0]["winner_team_id"] = fixtures[0]["team_a_id"]
    write_json(tmp_path / "fixtures.json", fixtures)

    errors = validate_processed_data(tmp_path)

    assert "A-1 is scheduled but winner_team_id is not null" in errors


def test_validate_processed_data_rejects_finished_winner_mismatch(
    tmp_path: Path,
) -> None:
    _write_valid_dataset(tmp_path)
    fixtures = json.loads((tmp_path / "fixtures.json").read_text())
    fixture = fixtures[0]
    fixture["status"] = "finished"
    fixture["result"] = {
        "played": True,
        "team_a_goals": 2,
        "team_b_goals": 0,
    }
    fixture["winner_team_id"] = fixture["team_b_id"]
    write_json(tmp_path / "fixtures.json", fixtures)
    write_json(
        tmp_path / "results.json",
        [
            {
                "match_id": fixture["id"],
                "team_a_id": fixture["team_a_id"],
                "team_b_id": fixture["team_b_id"],
                "team_a_goals": 2,
                "team_b_goals": 0,
                "status": "finished",
            }
        ],
    )

    errors = validate_processed_data(tmp_path)

    assert "A-1 winner_team_id does not match result" in errors


def test_validate_processed_data_rejects_results_score_mismatch(
    tmp_path: Path,
) -> None:
    _write_valid_dataset(tmp_path)
    fixtures = json.loads((tmp_path / "fixtures.json").read_text())
    fixture = fixtures[0]
    fixture["status"] = "finished"
    fixture["result"] = {
        "played": True,
        "team_a_goals": 2,
        "team_b_goals": 0,
    }
    fixture["winner_team_id"] = fixture["team_a_id"]
    write_json(tmp_path / "fixtures.json", fixtures)
    write_json(
        tmp_path / "results.json",
        [
            {
                "match_id": fixture["id"],
                "team_a_id": fixture["team_a_id"],
                "team_b_id": fixture["team_b_id"],
                "team_a_goals": 1,
                "team_b_goals": 0,
                "status": "finished",
            }
        ],
    )

    errors = validate_processed_data(tmp_path)

    assert "A-1 result score does not match fixtures.json" in errors

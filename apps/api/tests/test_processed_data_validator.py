"""Tests for processed World Cup data validation."""

import sys
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
                    "kickoff": None,
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
    fixtures = __import__("json").loads((tmp_path / "fixtures.json").read_text())
    fixtures[0]["group_id"] = "B"
    write_json(tmp_path / "fixtures.json", fixtures)

    errors = validate_processed_data(tmp_path)

    assert any("is not in B" in error for error in errors)


def test_validate_processed_data_rejects_missing_metadata(tmp_path: Path) -> None:
    _write_valid_dataset(tmp_path)
    metadata = __import__("json").loads((tmp_path / "metadata.json").read_text())
    del metadata["rating_source"]
    write_json(tmp_path / "metadata.json", metadata)

    errors = validate_processed_data(tmp_path)

    assert "metadata missing rating_source" in errors

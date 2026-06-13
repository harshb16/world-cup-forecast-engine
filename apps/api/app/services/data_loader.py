"""Data loading service."""

import json
from pathlib import Path
from typing import Any

from app.models.domain import Group, Match, Team, TournamentConfig

REPO_ROOT = Path(__file__).resolve().parents[4]
SAMPLE_DATA_DIR = REPO_ROOT / "data" / "sample"
PROCESSED_DATA_DIR = REPO_ROOT / "data" / "processed"


def _load_json(path: str | Path) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, list):
        raise ValueError(f"expected a JSON list in {path}")
    return data


def _load_object(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object in {path}")
    return data


def load_teams(path: str | Path) -> list[Team]:
    """Load team records from JSON."""
    return [Team.model_validate(item) for item in _load_json(path)]


def load_groups(path: str | Path) -> list[Group]:
    """Load group records from JSON."""
    return [Group.model_validate(item) for item in _load_json(path)]


def load_matches(path: str | Path) -> list[Match]:
    """Load match records from JSON."""
    return [Match.model_validate(item) for item in _load_json(path)]


def load_sample_tournament() -> TournamentConfig:
    """Load the local 48-team sample tournament."""
    teams = load_teams(SAMPLE_DATA_DIR / "sample_teams.json")
    groups = load_groups(SAMPLE_DATA_DIR / "sample_groups.json")
    matches = load_matches(SAMPLE_DATA_DIR / "sample_fixtures.json")

    return TournamentConfig(teams=teams, groups=groups, matches=matches)


def load_processed_tournament() -> TournamentConfig:
    """Load checked-in processed World Cup 2026 data."""
    teams = load_teams(PROCESSED_DATA_DIR / "teams.json")
    groups = load_groups(PROCESSED_DATA_DIR / "groups.json")
    matches = load_matches(PROCESSED_DATA_DIR / "fixtures.json")

    return TournamentConfig(teams=teams, groups=groups, matches=matches)


def load_tournament(mode: str) -> TournamentConfig:
    """Load tournament data for the selected mode."""
    if mode == "sample":
        return load_sample_tournament()
    if mode == "processed":
        return load_processed_tournament()
    raise ValueError(f"unsupported data mode: {mode}")


def load_metadata(mode: str) -> dict[str, Any]:
    """Load data-source metadata for the selected mode."""
    if mode == "processed":
        return _load_object(PROCESSED_DATA_DIR / "metadata.json")
    if mode == "sample":
        return {
            "data_mode": "sample",
            "is_real_data": False,
            "data_version": "sample-dev",
            "last_updated": None,
            "sources": [],
            "rating_source": "sample",
            "ratings_are_official": False,
            "bracket_status": "sample development data",
        }
    raise ValueError(f"unsupported data mode: {mode}")

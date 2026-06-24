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
        metadata = _load_object(PROCESSED_DATA_DIR / "metadata.json")
        return {**metadata, **_processed_quality_metadata()}
    if mode == "sample":
        sample = load_sample_tournament()
        return {
            "data_mode": "sample",
            "is_real_data": False,
            "data_version": "sample-dev",
            "last_updated": None,
            "sources": [],
            "rating_source": "sample",
            "ratings_are_official": False,
            "bracket_status": "sample development data",
            "team_count": len(sample.teams),
            "group_count": len(sample.groups),
            "fixture_count": len(sample.matches),
            "completed_result_count": sum(
                1
                for match in sample.matches
                if match.result is not None and match.result.played
            ),
            "rating_coverage_count": len(sample.teams),
            "data_quality_notes": [
                "Sample mode uses generated development teams and fixtures.",
                "Use processed mode for checked-in World Cup 2026 data.",
            ],
            "model_limitations": [
                "Sample ratings are synthetic and should not be read as team strength.",
                "Knockout bracket uses FIFA World Cup 2026 round-of-32 slots with deterministic third-place assignment.",
            ],
        }
    raise ValueError(f"unsupported data mode: {mode}")


def load_model_parameters(mode: str) -> dict[str, Any]:
    """Load model parameter metadata for the selected mode."""
    if mode == "processed":
        return _load_object(PROCESSED_DATA_DIR / "model_parameters.json")
    if mode == "sample":
        return {
            "data_version": "sample-model-parameters",
            "source": {},
            "team_ratings": [],
        }
    raise ValueError(f"unsupported data mode: {mode}")


def load_squad_features(mode: str) -> dict[str, dict[str, float]]:
    """Load computed squad features for active teams when available."""
    if mode != "processed":
        return {}

    path = PROCESSED_DATA_DIR / "squad_features.json"
    if not path.exists():
        return {}

    data = _load_json(path)
    return {
        str(item["team_id"]): {
            key: float(value)
            for key, value in item.items()
            if key != "team_id" and isinstance(value, (int, float))
        }
        for item in data
    }


def _processed_quality_metadata() -> dict[str, Any]:
    tournament = load_processed_tournament()
    ratings = _load_json(PROCESSED_DATA_DIR / "ratings.json")
    rated_team_ids = {item["team_id"] for item in ratings}
    completed_result_count = sum(
        1
        for match in tournament.matches
        if match.result is not None and match.result.played
    )

    return {
        "team_count": len(tournament.teams),
        "group_count": len(tournament.groups),
        "fixture_count": len(tournament.matches),
        "completed_result_count": completed_result_count,
        "rating_coverage_count": len(
            {team.id for team in tournament.teams if team.id in rated_team_ids}
        ),
        "data_quality_notes": [
            "Processed mode uses checked-in World Cup 2026 teams, groups, fixtures, results, rating references, and open-data Elo parameters.",
            "Completed results are included only when present in processed fixtures.",
            "The public default uses open-data Elo ratings; FIFA rank-derived ratings remain available only to baseline and comparison models.",
        ],
        "model_limitations": [
            "The GBM uses a small real-result sample supplemented by synthetic Oracle v2 labels.",
            "Oracle v3 ensemble weights are fixed rather than re-fit after every matchday.",
            "Knockout bracket uses FIFA World Cup 2026 round-of-32 slots with deterministic third-place assignment.",
            "Group and third-place ties currently use points, goal difference, goals scored, then team ID; full FIFA head-to-head and fair-play ordering is not implemented.",
            "Small Monte Carlo probability gaps can be sampling noise.",
        ],
    }

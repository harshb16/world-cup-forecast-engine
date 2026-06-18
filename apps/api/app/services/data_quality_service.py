"""Data quality reporting for tournament inputs."""

from datetime import UTC, datetime
from typing import Any

from app.models.schemas import DataQualityResponse, TeamDataQualityResponse
from app.services.data_loader import (
    PROCESSED_DATA_DIR,
    load_metadata,
    load_squad_features,
    load_tournament,
)


def calculate_data_quality(data_mode: str) -> DataQualityResponse:
    """Build coverage report for active tournament data sources."""
    metadata = load_metadata(data_mode)
    tournament = load_tournament(data_mode)
    squad_features = load_squad_features(data_mode)

    ratings_path = PROCESSED_DATA_DIR / "ratings.json"
    rated_team_ids: set[str] = set()
    if data_mode == "processed" and ratings_path.exists():
        import json

        ratings = json.loads(ratings_path.read_text())
        rated_team_ids = {item["team_id"] for item in ratings}

    completed_results = sum(
        1
        for match in tournament.matches
        if match.result is not None and match.result.played
    )
    group_fixtures = [match for match in tournament.matches if match.stage == "group"]

    teams: list[TeamDataQualityResponse] = []
    missing_squad: list[str] = []
    missing_ratings: list[str] = []
    low_coverage: list[str] = []

    for team in tournament.teams:
        squad = squad_features.get(team.id, {})
        coverage = float(squad.get("coverage", 0.0)) if squad else 0.0
        has_rating = team.id in rated_team_ids if data_mode == "processed" else True
        has_squad = bool(squad)
        warnings: list[str] = []

        if not has_rating:
            missing_ratings.append(team.id)
            warnings.append("Missing rank-derived rating.")
        if not has_squad:
            missing_squad.append(team.id)
            warnings.append("Missing squad feature coverage.")
        elif coverage < 0.75:
            low_coverage.append(team.id)
            warnings.append("Squad alias coverage is partial.")

        teams.append(
            TeamDataQualityResponse(
                team_id=team.id,
                team_name=team.name,
                group_id=team.group_id,
                has_rating=has_rating,
                has_squad_features=has_squad,
                squad_coverage=coverage if has_squad else None,
                alias_confidence=coverage if has_squad else None,
                missing_features=_missing_feature_labels(has_rating, has_squad, coverage),
                warnings=warnings,
            )
        )

    source_coverage = {
        "teams": len(tournament.teams),
        "groups": len(tournament.groups),
        "group_fixtures": len(group_fixtures),
        "completed_results": completed_results,
        "ratings": len(rated_team_ids) if data_mode == "processed" else len(tournament.teams),
        "squad_features": len(squad_features),
    }

    global_warnings: list[str] = []
    if missing_ratings:
        global_warnings.append(
            f"{len(missing_ratings)} teams missing ratings coverage."
        )
    if missing_squad:
        global_warnings.append(
            f"{len(missing_squad)} teams missing squad feature rows."
        )
    if low_coverage:
        global_warnings.append(
            f"{len(low_coverage)} teams have partial squad alias coverage."
        )

    return DataQualityResponse(
        data_mode=data_mode,
        last_refresh=metadata.get("last_updated")
        or datetime.now(tz=UTC).isoformat(),
        source_coverage=source_coverage,
        teams=teams,
        missing_squad_features=missing_squad,
        missing_ratings=missing_ratings,
        low_alias_coverage=low_coverage,
        warnings=global_warnings,
        notes=[
            "Ratings are rank-derived model inputs, not official FIFA strength scores.",
            "Squad features come from Transfermarkt datasets with alias matching.",
            "Availability is represented as computed squad coverage, not live injury feeds.",
        ],
    )


def build_data_quality_payload(data_mode: str) -> dict[str, Any]:
    """Return serializable data quality payload for processed JSON export."""
    report = calculate_data_quality(data_mode)
    return report.model_dump()


def _missing_feature_labels(
    has_rating: bool,
    has_squad: bool,
    coverage: float,
) -> list[str]:
    missing: list[str] = []
    if not has_rating:
        missing.append("rating")
    if not has_squad:
        missing.append("squad_features")
    elif coverage < 1.0:
        missing.append("full_squad_alias")
    return missing

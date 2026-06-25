"""Pre-aggregated outlook helpers for published forecast snapshots."""

from __future__ import annotations

import math

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.domain import Match, Team, TournamentConfig
from app.models.schemas import (
    ForecastFixtureOutlookResponse,
    ForecastUncertaintyResponse,
    ModelType,
)
from app.services.simulation_service import create_match_model


def build_upcoming_fixture_outlook(
    config: TournamentConfig,
    *,
    data_mode: str,
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    limit: int = 12,
) -> list[ForecastFixtureOutlookResponse]:
    """Return model outlook for the next unplayed group fixtures."""
    match_model = create_match_model(model_type, data_mode)
    teams_by_id: dict[str, Team] = {team.id: team for team in config.teams}
    candidates = [
        match
        for match in config.matches
        if match.stage == "group"
        and (match.result is None or not match.result.played)
    ]
    candidates.sort(key=_kickoff_sort_key)
    outlook: list[ForecastFixtureOutlookResponse] = []
    for match in candidates[:limit]:
        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        probabilities = match_model.predict_probabilities(team_a, team_b)
        team_a_xg, team_b_xg = _expected_goals(match_model, team_a, team_b)
        outlook.append(
            ForecastFixtureOutlookResponse(
                match_id=match.id,
                group_id=match.group_id,
                kickoff_utc=_kickoff_utc(match),
                team_a_id=team_a.id,
                team_a_name=team_a.name,
                team_b_id=team_b.id,
                team_b_name=team_b.name,
                team_a_win=probabilities["team_a_win"],
                draw=probabilities["draw"],
                team_b_win=probabilities["team_b_win"],
                team_a_expected_goals=team_a_xg,
                team_b_expected_goals=team_b_xg,
            )
        )
    return outlook


def build_champion_uncertainty(
    champion_probabilities: dict[str, float],
    *,
    n_simulations: int,
    top_n: int = 12,
) -> ForecastUncertaintyResponse:
    """Return standard errors for the leading champion probabilities."""
    if n_simulations <= 0:
        return ForecastUncertaintyResponse(
            n_simulations=n_simulations,
            champion_standard_error={},
        )
    leaders = sorted(
        champion_probabilities.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:top_n]
    standard_errors = {
        team_id: math.sqrt(max(probability, 0.0) * (1 - probability) / n_simulations)
        for team_id, probability in leaders
        if probability > 0
    }
    return ForecastUncertaintyResponse(
        n_simulations=n_simulations,
        champion_standard_error=standard_errors,
    )


def _kickoff_sort_key(match: Match) -> tuple[int, str]:
    kickoff = _kickoff_utc(match)
    return (0 if kickoff else 1, kickoff or match.id)


def _kickoff_utc(match: Match) -> str | None:
    extra = getattr(match, "kickoff_utc", None)
    if isinstance(extra, str) and extra:
        return extra
    return None


def _expected_goals(match_model, team_a: Team, team_b: Team) -> tuple[float, float]:
    if hasattr(match_model, "expected_goals"):
        return match_model.expected_goals(team_a, team_b)
    probabilities = match_model.predict_probabilities(team_a, team_b)
    total = probabilities["team_a_win"] + probabilities["team_b_win"]
    if total <= 0:
        return 1.1, 1.1
    team_a_share = probabilities["team_a_win"] / total
    baseline = 2.4
    return baseline * team_a_share, baseline * (1 - team_a_share)

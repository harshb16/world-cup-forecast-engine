"""Knockout extra time, penalties, and host-nation adjustments."""

from __future__ import annotations

import numpy as np

from app.models.domain import MatchResult, Team
from app.simulation.match_models import MatchModel

HOST_NATION_IDS = frozenset({"USA", "CANADA", "MEXICO"})
HOST_ADVANTAGE_RATING = 40.0
EXTRA_TIME_GOAL_SCALE = 1 / 3


def with_host_advantage(team: Team) -> Team:
    """Apply co-host rating boost for USA, Canada, and Mexico."""
    if team.id in HOST_NATION_IDS:
        return team.model_copy(update={"rating": team.rating + HOST_ADVANTAGE_RATING})
    return team


def resolve_knockout_match(
    match_model: MatchModel,
    team_a: Team,
    team_b: Team,
    rng: np.random.Generator,
) -> tuple[MatchResult, str]:
    """Simulate regulation, extra time, and penalties when needed."""
    adjusted_a = with_host_advantage(team_a)
    adjusted_b = with_host_advantage(team_b)
    regulation = _simulate_period(match_model, adjusted_a, adjusted_b, rng, stage="knockout")
    if regulation.team_a_goals != regulation.team_b_goals:
        return regulation, _winner_from_goals(team_a, team_b, regulation)

    extra_time = _simulate_extra_time(match_model, adjusted_a, adjusted_b, rng)
    total = MatchResult(
        team_a_goals=regulation.team_a_goals + extra_time.team_a_goals,
        team_b_goals=regulation.team_b_goals + extra_time.team_b_goals,
        played=True,
    )
    if total.team_a_goals != total.team_b_goals:
        return total, _winner_from_goals(team_a, team_b, total)

    return total, _penalty_winner(adjusted_a, adjusted_b, rng)


def _simulate_period(
    match_model: MatchModel,
    team_a: Team,
    team_b: Team,
    rng: np.random.Generator,
    *,
    stage: str | None,
) -> MatchResult:
    if hasattr(match_model, "simulate_result"):
        try:
            return match_model.simulate_result(team_a, team_b, rng, stage=stage)
        except TypeError:
            return match_model.simulate_result(team_a, team_b, rng)
    return match_model.simulate_result(team_a, team_b, rng)


def _simulate_extra_time(
    match_model: MatchModel,
    team_a: Team,
    team_b: Team,
    rng: np.random.Generator,
) -> MatchResult:
    if hasattr(match_model, "simulate_result"):
        try:
            return match_model.simulate_result(team_a, team_b, rng, stage="extra_time")
        except TypeError:
            pass
    if hasattr(match_model, "expected_goals"):
        try:
            team_a_expected, team_b_expected = match_model.expected_goals(
                team_a,
                team_b,
                stage="knockout",
            )
        except TypeError:
            team_a_expected, team_b_expected = match_model.expected_goals(team_a, team_b)
        team_a_expected *= EXTRA_TIME_GOAL_SCALE
        team_b_expected *= EXTRA_TIME_GOAL_SCALE
        return MatchResult(
            team_a_goals=int(rng.poisson(max(team_a_expected, 0.05))),
            team_b_goals=int(rng.poisson(max(team_b_expected, 0.05))),
            played=True,
        )
    return MatchResult(
        team_a_goals=int(rng.random() < 0.12),
        team_b_goals=int(rng.random() < 0.12),
        played=True,
    )


def _winner_from_goals(team_a: Team, team_b: Team, result: MatchResult) -> str:
    if result.team_a_goals > result.team_b_goals:
        return team_a.id
    if result.team_b_goals > result.team_a_goals:
        return team_b.id
    raise ValueError("knockout match result is still tied after resolution")


def _penalty_winner(team_a: Team, team_b: Team, rng: np.random.Generator) -> str:
    rating_gap = team_a.rating - team_b.rating
    team_a_probability = 1 / (1 + 10 ** (-rating_gap / 200))
    return team_a.id if rng.random() < team_a_probability else team_b.id

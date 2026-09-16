"""Tests for knockout extra time and penalty resolution."""

from __future__ import annotations

import numpy as np

from app.models.domain import MatchResult, Team
from app.simulation.knockout_resolution import (
    HOST_ADVANTAGE_RATING,
    resolve_knockout_match,
    with_host_advantage,
)


class _SequenceKnockoutModel:
    def __init__(
        self,
        regulation: MatchResult,
        extra_time: MatchResult | None = None,
    ) -> None:
        self.regulation = regulation
        self.extra_time = extra_time or MatchResult(team_a_goals=0, team_b_goals=0)

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        return {"team_a_win": 0.4, "draw": 0.2, "team_b_win": 0.4}

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
        stage: str | None = None,
    ) -> MatchResult:
        if stage == "extra_time":
            return self.extra_time
        return self.regulation


def test_regulation_winner_skips_extra_time() -> None:
    model = _SequenceKnockoutModel(MatchResult(team_a_goals=2, team_b_goals=1))
    result, winner = resolve_knockout_match(
        model,
        _team("USA"),
        _team("BRA"),
        np.random.default_rng(1),
    )
    assert result.team_a_goals == 2
    assert winner == "USA"


def test_drawn_regulation_can_resolve_in_extra_time() -> None:
    model = _SequenceKnockoutModel(
        MatchResult(team_a_goals=1, team_b_goals=1),
        MatchResult(team_a_goals=1, team_b_goals=0),
    )
    result, winner = resolve_knockout_match(
        model,
        _team("USA"),
        _team("BRA"),
        np.random.default_rng(2),
    )
    assert result.team_a_goals == 2
    assert result.team_b_goals == 1
    assert winner == "USA"


def test_level_after_extra_time_uses_penalties() -> None:
    model = _SequenceKnockoutModel(
        MatchResult(team_a_goals=0, team_b_goals=0),
        MatchResult(team_a_goals=0, team_b_goals=0),
    )
    _, winner = resolve_knockout_match(
        model,
        _team("USA", rating=1700),
        _team("BRA", rating=1500),
        np.random.default_rng(0),
    )
    assert winner == "USA"


def _team(team_id: str, rating: float = 1500.0) -> Team:
    return Team(id=team_id, name=team_id, group_id="A", rating=rating)


def test_host_nation_receives_rating_boost() -> None:
    boosted = with_host_advantage(_team("MEXICO", rating=1500))
    assert boosted.rating == 1500 + HOST_ADVANTAGE_RATING

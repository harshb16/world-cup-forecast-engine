"""Match model implementations."""

from typing import Protocol

import numpy as np

from app.models.domain import MatchResult, Team

WIN_SCORELINES = [(1, 0), (2, 0), (2, 1), (3, 1)]
DRAW_SCORELINES = [(0, 0), (1, 1), (2, 2)]


class MatchModel(Protocol):
    """Interface for match prediction and simulation models."""

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        """Return win/draw/loss probabilities for team A and team B."""
        ...

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
    ) -> MatchResult:
        """Simulate one match result."""
        ...


class EloWinDrawLossModel:
    """Simple Elo-derived win/draw/loss model."""

    def __init__(self, base_draw_probability: float = 0.26) -> None:
        if not 0 <= base_draw_probability < 1:
            raise ValueError("base_draw_probability must be in [0, 1)")
        self.base_draw_probability = base_draw_probability

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        """Predict team A win, draw, and team B win probabilities."""
        rating_gap = team_a.rating - team_b.rating
        expected_a = 1 / (1 + 10 ** (-rating_gap / 400))
        draw_reduction = min(abs(rating_gap) / 2000, 0.1)
        draw_probability = max(0.12, self.base_draw_probability - draw_reduction)
        decisive_probability = 1 - draw_probability

        team_a_win = decisive_probability * expected_a
        team_b_win = decisive_probability * (1 - expected_a)

        return {
            "team_a_win": team_a_win,
            "draw": draw_probability,
            "team_b_win": team_b_win,
        }

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
    ) -> MatchResult:
        """Simulate a scoreline from the predicted W/D/L probabilities."""
        probabilities = self.predict_probabilities(team_a, team_b)
        outcome = rng.choice(
            ["team_a_win", "draw", "team_b_win"],
            p=[
                probabilities["team_a_win"],
                probabilities["draw"],
                probabilities["team_b_win"],
            ],
        )

        if outcome == "draw":
            team_a_goals, team_b_goals = DRAW_SCORELINES[int(rng.integers(len(DRAW_SCORELINES)))]
        elif outcome == "team_a_win":
            team_a_goals, team_b_goals = WIN_SCORELINES[int(rng.integers(len(WIN_SCORELINES)))]
        else:
            team_b_goals, team_a_goals = WIN_SCORELINES[int(rng.integers(len(WIN_SCORELINES)))]

        return MatchResult(
            team_a_goals=int(team_a_goals),
            team_b_goals=int(team_b_goals),
        )

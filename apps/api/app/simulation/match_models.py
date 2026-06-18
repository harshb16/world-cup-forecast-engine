"""Match model implementations."""

import math
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

    def __init__(
        self,
        base_draw_probability: float = 0.26,
        rating_overrides: dict[str, float] | None = None,
    ) -> None:
        if not 0 <= base_draw_probability < 1:
            raise ValueError("base_draw_probability must be in [0, 1)")
        self.base_draw_probability = base_draw_probability
        self.rating_overrides = rating_overrides or {}

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        """Predict team A win, draw, and team B win probabilities."""
        rating_gap = self.rating_for(team_a) - self.rating_for(team_b)
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

    def rating_for(self, team: Team) -> float:
        """Return the model rating used for this team."""
        return self.rating_overrides.get(team.id, team.rating)


def expected_goals(team_a: Team, team_b: Team) -> tuple[float, float]:
    """Convert team ratings into expected goals for each side."""
    base_goals = 1.35
    rating_gap = (team_a.rating - team_b.rating) / 400
    team_a_expected = base_goals * float(np.exp(rating_gap * 0.35))
    team_b_expected = base_goals * float(np.exp(-rating_gap * 0.35))

    return (
        min(max(team_a_expected, 0.3), 3.2),
        min(max(team_b_expected, 0.3), 3.2),
    )


class PoissonScoreModel:
    """Poisson scoreline model using rating-derived expected goals."""

    def expected_goals(self, team_a: Team, team_b: Team) -> tuple[float, float]:
        """Return expected goals for team A and team B."""
        return expected_goals(team_a, team_b)

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        """Approximate W/D/L probabilities by sampling many score probabilities."""
        team_a_expected, team_b_expected = self.expected_goals(team_a, team_b)
        max_goals = 8
        team_a_win = 0.0
        draw = 0.0
        team_b_win = 0.0

        for team_a_goals in range(max_goals + 1):
            prob_a = _poisson_probability(team_a_goals, team_a_expected)
            for team_b_goals in range(max_goals + 1):
                probability = prob_a * _poisson_probability(team_b_goals, team_b_expected)
                if team_a_goals > team_b_goals:
                    team_a_win += probability
                elif team_a_goals < team_b_goals:
                    team_b_win += probability
                else:
                    draw += probability

        total = team_a_win + draw + team_b_win
        return {
            "team_a_win": team_a_win / total,
            "draw": draw / total,
            "team_b_win": team_b_win / total,
        }

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
    ) -> MatchResult:
        """Simulate a football scoreline from Poisson goal distributions."""
        team_a_expected, team_b_expected = self.expected_goals(team_a, team_b)

        return MatchResult(
            team_a_goals=int(rng.poisson(team_a_expected)),
            team_b_goals=int(rng.poisson(team_b_expected)),
        )


class OracleV2Model:
    """Feature-blended Poisson model for stronger tournament projections."""

    def __init__(
        self,
        rating_overrides: dict[str, float] | None = None,
        squad_features: dict[str, dict[str, float]] | None = None,
    ) -> None:
        self.rating_overrides = rating_overrides or {}
        self.squad_features = squad_features or {}

    def rating_for(self, team: Team) -> float:
        calibrated_rating = self.rating_overrides.get(team.id, team.rating)
        squad_power = self.squad_features.get(team.id, {}).get("squad_power", team.rating)
        return (0.45 * team.rating) + (0.20 * calibrated_rating) + (0.35 * squad_power)

    def expected_goals(self, team_a: Team, team_b: Team) -> tuple[float, float]:
        team_a_attack = self._attack_strength(team_a)
        team_b_attack = self._attack_strength(team_b)
        team_a_defense = self._defense_strength(team_a)
        team_b_defense = self._defense_strength(team_b)

        team_a_expected = 1.28 * np.exp(((team_a_attack - team_b_defense) / 400) * 0.42)
        team_b_expected = 1.28 * np.exp(((team_b_attack - team_a_defense) / 400) * 0.42)
        return (
            float(min(max(team_a_expected, 0.25), 3.4)),
            float(min(max(team_b_expected, 0.25), 3.4)),
        )

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        team_a_expected, team_b_expected = self.expected_goals(team_a, team_b)
        return _scoreline_probabilities(team_a_expected, team_b_expected)

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
    ) -> MatchResult:
        team_a_expected, team_b_expected = self.expected_goals(team_a, team_b)
        return MatchResult(
            team_a_goals=int(rng.poisson(team_a_expected)),
            team_b_goals=int(rng.poisson(team_b_expected)),
        )

    def projected_result(self, team_a: Team, team_b: Team) -> MatchResult:
        """Return median-ish deterministic scoreline for favorite group tables."""
        team_a_expected, team_b_expected = self.expected_goals(team_a, team_b)
        team_a_goals = int(round(team_a_expected))
        team_b_goals = int(round(team_b_expected))
        if team_a_goals == team_b_goals:
            advance = self.predict_probabilities(team_a, team_b)
            if advance["team_a_win"] > advance["team_b_win"] + 0.08:
                team_a_goals += 1
            elif advance["team_b_win"] > advance["team_a_win"] + 0.08:
                team_b_goals += 1
        return MatchResult(
            team_a_goals=max(team_a_goals, 0),
            team_b_goals=max(team_b_goals, 0),
        )

    def _attack_strength(self, team: Team) -> float:
        features = self.squad_features.get(team.id, {})
        return self.rating_for(team) + features.get("attack_bonus", 0.0)

    def _defense_strength(self, team: Team) -> float:
        features = self.squad_features.get(team.id, {})
        return self.rating_for(team) + features.get("defense_bonus", 0.0)


class DixonColesModel:
    """Poisson model with Dixon-Coles low-score correlation correction."""

    DEFAULT_RHO = -0.13

    def __init__(
        self,
        rho: float = DEFAULT_RHO,
        rating_overrides: dict[str, float] | None = None,
        squad_features: dict[str, dict[str, float]] | None = None,
    ) -> None:
        self.rho = rho
        self.rating_overrides = rating_overrides or {}
        self.squad_features = squad_features or {}

    def expected_goals(self, team_a: Team, team_b: Team) -> tuple[float, float]:
        """Return expected goals using PoissonScoreModel logic."""
        return expected_goals(team_a, team_b)

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        """Predict W/D/L using Dixon-Coles corrected joint probability matrix."""
        mu, nu = self.expected_goals(team_a, team_b)
        max_goals = 8

        team_a_win = 0.0
        draw = 0.0
        team_b_win = 0.0
        total = 0.0

        for x in range(max_goals + 1):
            prob_x = _poisson_probability(x, mu)
            for y in range(max_goals + 1):
                prob_y = _poisson_probability(y, nu)
                corrected = prob_x * prob_y * _tau(x, y, mu, nu, self.rho)
                total += corrected
                if x > y:
                    team_a_win += corrected
                elif x < y:
                    team_b_win += corrected
                else:
                    draw += corrected

        return {
            "team_a_win": team_a_win / total,
            "draw": draw / total,
            "team_b_win": team_b_win / total,
        }

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
    ) -> MatchResult:
        """Sample a scoreline from the Dixon-Coles corrected joint distribution."""
        mu, nu = self.expected_goals(team_a, team_b)
        max_goals = 8
        n = max_goals + 1

        probs: list[float] = []
        pairs: list[tuple[int, int]] = []

        for x in range(n):
            prob_x = _poisson_probability(x, mu)
            for y in range(n):
                prob_y = _poisson_probability(y, nu)
                corrected = prob_x * prob_y * _tau(x, y, mu, nu, self.rho)
                probs.append(max(corrected, 0.0))
                pairs.append((x, y))

        total = sum(probs)
        normalized = [p / total for p in probs]
        chosen_index = int(rng.choice(len(pairs), p=normalized))
        team_a_goals, team_b_goals = pairs[chosen_index]
        return MatchResult(team_a_goals=team_a_goals, team_b_goals=team_b_goals)


def _tau(x: int, y: int, mu: float, nu: float, rho: float) -> float:
    """Dixon-Coles correction factor for low-score scorelines."""
    if x == 0 and y == 0:
        return 1.0 - mu * nu * rho
    if x == 0 and y == 1:
        return 1.0 + mu * rho
    if x == 1 and y == 0:
        return 1.0 + nu * rho
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def _scoreline_probabilities(
    team_a_expected: float,
    team_b_expected: float,
) -> dict[str, float]:
    max_goals = 8
    team_a_win = 0.0
    draw = 0.0
    team_b_win = 0.0

    for team_a_goals in range(max_goals + 1):
        prob_a = _poisson_probability(team_a_goals, team_a_expected)
        for team_b_goals in range(max_goals + 1):
            probability = prob_a * _poisson_probability(team_b_goals, team_b_expected)
            if team_a_goals > team_b_goals:
                team_a_win += probability
            elif team_a_goals < team_b_goals:
                team_b_win += probability
            else:
                draw += probability

    total = team_a_win + draw + team_b_win
    return {
        "team_a_win": team_a_win / total,
        "draw": draw / total,
        "team_b_win": team_b_win / total,
    }


def _poisson_probability(goals: int, expected: float) -> float:
    return float((expected**goals) * np.exp(-expected) / math.factorial(goals))

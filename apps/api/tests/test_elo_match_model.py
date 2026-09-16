"""Tests for the Elo win/draw/loss match model."""

import numpy as np
import pytest

from app.models.domain import Team
from app.simulation.match_models import EloWinDrawLossModel


def _team(team_id: str, rating: float) -> Team:
    return Team(id=team_id, name=f"Team {team_id}", group_id="A", rating=rating)


def test_probabilities_sum_to_one() -> None:
    model = EloWinDrawLossModel()
    probabilities = model.predict_probabilities(_team("T1", 1600), _team("T2", 1500))

    assert sum(probabilities.values()) == pytest.approx(1.0)


def test_equal_ratings_are_symmetric() -> None:
    model = EloWinDrawLossModel()
    probabilities = model.predict_probabilities(_team("T1", 1500), _team("T2", 1500))

    assert probabilities["team_a_win"] == pytest.approx(probabilities["team_b_win"])


def test_stronger_team_has_higher_win_probability() -> None:
    model = EloWinDrawLossModel()
    probabilities = model.predict_probabilities(_team("T1", 1700), _team("T2", 1400))

    assert probabilities["team_a_win"] > probabilities["team_b_win"]


def test_deterministic_simulation_with_fixed_rng_seed() -> None:
    model = EloWinDrawLossModel()
    team_a = _team("T1", 1600)
    team_b = _team("T2", 1500)

    result_a = model.simulate_result(team_a, team_b, np.random.default_rng(123))
    result_b = model.simulate_result(team_a, team_b, np.random.default_rng(123))

    assert result_a == result_b


def test_result_goals_are_non_negative_integers() -> None:
    model = EloWinDrawLossModel()
    result = model.simulate_result(_team("T1", 1600), _team("T2", 1500), np.random.default_rng(1))

    assert isinstance(result.team_a_goals, int)
    assert isinstance(result.team_b_goals, int)
    assert result.team_a_goals >= 0
    assert result.team_b_goals >= 0

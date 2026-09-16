"""Tests for the Poisson scoreline match model."""

import numpy as np
import pytest

from app.models.domain import Team
from app.simulation.match_models import PoissonScoreModel, expected_goals


def _team(team_id: str, rating: float) -> Team:
    return Team(id=team_id, name=f"Team {team_id}", group_id="A", rating=rating)


def test_goals_are_non_negative_integers() -> None:
    model = PoissonScoreModel()
    result = model.simulate_result(_team("T1", 1600), _team("T2", 1500), np.random.default_rng(1))

    assert isinstance(result.team_a_goals, int)
    assert isinstance(result.team_b_goals, int)
    assert result.team_a_goals >= 0
    assert result.team_b_goals >= 0


def test_deterministic_with_fixed_seed() -> None:
    model = PoissonScoreModel()
    team_a = _team("T1", 1600)
    team_b = _team("T2", 1500)

    result_a = model.simulate_result(team_a, team_b, np.random.default_rng(123))
    result_b = model.simulate_result(team_a, team_b, np.random.default_rng(123))

    assert result_a == result_b


def test_stronger_team_has_higher_average_goals() -> None:
    model = PoissonScoreModel()
    team_a = _team("T1", 1800)
    team_b = _team("T2", 1300)
    rng = np.random.default_rng(7)
    results = [model.simulate_result(team_a, team_b, rng) for _ in range(300)]

    average_a = sum(result.team_a_goals for result in results) / len(results)
    average_b = sum(result.team_b_goals for result in results) / len(results)

    assert average_a > average_b


def test_equal_teams_have_similar_expected_goals() -> None:
    team_a_expected, team_b_expected = expected_goals(_team("T1", 1500), _team("T2", 1500))

    assert team_a_expected == pytest.approx(team_b_expected)


def test_stronger_team_has_higher_expected_goals() -> None:
    team_a_expected, team_b_expected = expected_goals(_team("T1", 1750), _team("T2", 1450))

    assert team_a_expected > team_b_expected

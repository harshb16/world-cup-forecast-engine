"""Tests for Oracle v3 ensemble model."""

import numpy as np
import pytest

from app.models.domain import Team
from app.simulation.match_models import DixonColesModel, OracleV2Model, OracleV3Model


def _team(team_id: str, rating: float) -> Team:
    return Team(id=team_id, name=team_id, group_id="A", rating=rating)


def test_oracle_v3_blended_probabilities_sum_to_one() -> None:
    model = OracleV3Model(oracle_v2=OracleV2Model(), gbm=None)
    probabilities = model.predict_probabilities(_team("A", 1800), _team("B", 1600))
    total = sum(probabilities.values())
    assert total == pytest.approx(1.0)


def test_oracle_v3_fallback_weights_without_gbm() -> None:
    model = OracleV3Model(oracle_v2=OracleV2Model(), gbm=None)
    assert model.weights["gbm"] == 0.0
    assert model.weights["dixon_coles"] == pytest.approx(0.5)
    assert model.weights["oracle_v2"] == pytest.approx(0.5)


def test_oracle_v3_simulation_is_deterministic_with_seed() -> None:
    model = OracleV3Model(
        oracle_v2=OracleV2Model(),
        dixon_coles=DixonColesModel(),
        gbm=None,
    )
    team_a = _team("A", 1850)
    team_b = _team("B", 1700)
    rng_a = np.random.default_rng(7)
    rng_b = np.random.default_rng(7)
    first = model.simulate_result(team_a, team_b, rng_a)
    second = model.simulate_result(team_a, team_b, rng_b)
    assert first.team_a_goals == second.team_a_goals
    assert first.team_b_goals == second.team_b_goals


def test_oracle_v3_exposes_knockout_scale_from_oracle_v2() -> None:
    model = OracleV3Model(
        oracle_v2=OracleV2Model(knockout_lambda_scale=0.84),
        gbm=None,
    )

    assert model.knockout_lambda_scale == pytest.approx(0.84)

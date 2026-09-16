"""Tests for knockout expected-goals calibration on Forecast v2."""

import pytest

from app.models.domain import Team
from app.simulation.match_models import OracleV2Model


def _team(team_id: str, rating: float) -> Team:
    return Team(id=team_id, name=team_id, group_id="A", rating=rating)


def test_oracle_v2_knockout_expected_goals_are_scaled_down() -> None:
    model = OracleV2Model(knockout_lambda_scale=0.88)
    team_a = _team("A", 1900)
    team_b = _team("B", 1700)
    group_goals = model.expected_goals(team_a, team_b, stage="group")
    knockout_goals = model.expected_goals(team_a, team_b, stage="knockout")
    assert knockout_goals[0] == pytest.approx(group_goals[0] * 0.88)
    assert knockout_goals[1] == pytest.approx(group_goals[1] * 0.88)

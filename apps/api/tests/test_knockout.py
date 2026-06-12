"""Tests for knockout simulation."""

import numpy as np

from app.models.domain import MatchResult
from app.services.data_loader import load_sample_tournament
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import simulate_knockout
from app.simulation.match_models import EloWinDrawLossModel


class AlwaysDrawModel(EloWinDrawLossModel):
    def simulate_result(self, *args, **kwargs) -> MatchResult:  # type: ignore[no-untyped-def]
        return MatchResult(team_a_goals=1, team_b_goals=1)


def _qualified_team_ids() -> list[str]:
    config = load_sample_tournament()
    group_stage = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(1))
    return group_stage.qualified_team_ids


def _teams_by_id():
    config = load_sample_tournament()
    return {team.id: team for team in config.teams}


def test_exactly_one_champion() -> None:
    result = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(1),
    )

    assert result.champion_team_id


def test_exactly_two_finalists() -> None:
    result = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(1),
    )

    assert len(result.finalists) == 2


def test_no_knockout_match_has_missing_winner() -> None:
    result = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        AlwaysDrawModel(),
        np.random.default_rng(1),
    )

    assert all(match.winner_team_id for matches in result.rounds.values() for match in matches)


def test_deterministic_with_fixed_seed() -> None:
    result_a = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(123),
    )
    result_b = simulate_knockout(
        _qualified_team_ids(),
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(123),
    )

    assert result_a == result_b


def test_every_qualified_team_receives_final_stage_status() -> None:
    qualified_team_ids = _qualified_team_ids()
    result = simulate_knockout(
        qualified_team_ids,
        _teams_by_id(),
        EloWinDrawLossModel(),
        np.random.default_rng(1),
    )

    assert set(result.eliminated_stage_by_team) == set(qualified_team_ids)

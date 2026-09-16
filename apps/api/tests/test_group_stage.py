"""Tests for group-stage simulation."""

import numpy as np

from app.models.domain import MatchResult
from app.services.data_loader import load_sample_tournament
from app.simulation.group_stage import simulate_group_stage
from app.simulation.match_models import EloWinDrawLossModel


def test_already_played_results_are_preserved() -> None:
    config = load_sample_tournament()
    played_result = MatchResult(team_a_goals=4, team_b_goals=1)
    first_match = config.matches[0].model_copy(update={"result": played_result})
    config = config.model_copy(update={"matches": [first_match, *config.matches[1:]]})

    result = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(1))

    assert result.simulated_matches[0].result == played_result


def test_all_groups_produce_tables() -> None:
    config = load_sample_tournament()

    result = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(1))

    assert set(result.group_tables) == {group.id for group in config.groups}
    assert all(len(table) == 4 for table in result.group_tables.values())


def test_exactly_24_top_two_teams_qualify() -> None:
    config = load_sample_tournament()

    result = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(1))

    assert len(result.top_two_qualifiers) == 24


def test_exactly_eight_third_place_teams_qualify() -> None:
    config = load_sample_tournament()

    result = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(1))

    assert len(result.third_place_qualifiers) == 8


def test_exactly_32_teams_qualify_total() -> None:
    config = load_sample_tournament()

    result = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(1))

    assert len(result.qualified_team_ids) == 32
    assert len(set(result.qualified_team_ids)) == 32


def test_deterministic_with_fixed_seed() -> None:
    config = load_sample_tournament()

    result_a = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(123))
    result_b = simulate_group_stage(config, EloWinDrawLossModel(), np.random.default_rng(123))

    assert result_a == result_b

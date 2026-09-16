"""Tests for Monte Carlo tournament simulation."""

import pytest

from app.services.data_loader import load_sample_tournament
from app.simulation.match_models import EloWinDrawLossModel
from app.simulation.monte_carlo import STAGES, run_simulations


def _summary(n_simulations: int = 8, seed: int = 1):
    return run_simulations(
        load_sample_tournament(),
        EloWinDrawLossModel(),
        n_simulations=n_simulations,
        seed=seed,
    )


def test_output_contains_all_48_teams() -> None:
    summary = _summary()

    assert len(summary.stage_probabilities) == 48
    assert len(summary.average_points_by_team) == 48


def test_every_probability_is_between_zero_and_one() -> None:
    summary = _summary()
    probability_maps = [
        *summary.stage_probabilities.values(),
        summary.group_qualification_probability,
        summary.top_two_probability,
        summary.third_place_finish_probability,
        summary.third_place_qualification_probability,
    ]

    for probability_map in probability_maps:
        for probability in probability_map.values():
            assert 0 <= probability <= 1


def test_champion_probabilities_sum_approximately_to_one() -> None:
    summary = _summary(n_simulations=10)

    champion_total = sum(
        team_probabilities["champion"]
        for team_probabilities in summary.stage_probabilities.values()
    )

    assert champion_total == pytest.approx(1.0)


def test_deterministic_with_same_seed() -> None:
    summary_a = _summary(seed=123)
    summary_b = _summary(seed=123)

    assert summary_a == summary_b


def test_different_seeds_can_produce_different_outputs() -> None:
    summary_a = _summary(n_simulations=12, seed=1)
    summary_b = _summary(n_simulations=12, seed=2)

    assert summary_a != summary_b


def test_no_impossible_stage_probabilities() -> None:
    summary = _summary(n_simulations=10)

    for team_probabilities in summary.stage_probabilities.values():
        assert set(team_probabilities) == set(STAGES)
        assert sum(team_probabilities.values()) == pytest.approx(1.0)

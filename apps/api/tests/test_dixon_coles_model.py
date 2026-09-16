"""Tests for DixonColesModel."""

import numpy as np
import pytest

from app.models.domain import Team
from app.simulation.match_models import DixonColesModel, PoissonScoreModel, _tau


def _make_team(team_id: str, rating: float, group_id: str = "A") -> Team:
    return Team(id=team_id, name=team_id, rating=rating, group_id=group_id)


STRONG = _make_team("strong", 1800.0)
WEAK = _make_team("weak", 1400.0)
EQUAL_A = _make_team("equal_a", 1600.0)
EQUAL_B = _make_team("equal_b", 1600.0)


class TestTauCorrection:
    def test_0_0_reduces_with_negative_rho(self) -> None:
        """With rho=-0.13, tau(0,0) = 1 - mu*nu*rho > 1 for positive mu,nu."""
        result = _tau(0, 0, 1.3, 1.2, -0.13)
        assert result > 1.0

    def test_0_0_identity_at_zero_rho(self) -> None:
        assert _tau(0, 0, 1.3, 1.2, 0.0) == pytest.approx(1.0)

    def test_0_1(self) -> None:
        # 1 + mu*rho with rho=-0.13: should be < 1
        result = _tau(0, 1, 1.3, 1.2, -0.13)
        assert result == pytest.approx(1.0 + 1.3 * (-0.13))

    def test_1_0(self) -> None:
        result = _tau(1, 0, 1.3, 1.2, -0.13)
        assert result == pytest.approx(1.0 + 1.2 * (-0.13))

    def test_1_1(self) -> None:
        result = _tau(1, 1, 1.3, 1.2, -0.13)
        assert result == pytest.approx(1.0 - (-0.13))

    def test_other_scorelines_are_identity(self) -> None:
        for x, y in [(2, 0), (0, 2), (3, 3), (5, 1)]:
            assert _tau(x, y, 1.3, 1.2, -0.13) == pytest.approx(1.0)


class TestDixonColesVsPoisson:
    def test_0_0_probability_differs_from_pure_poisson(self) -> None:
        """Dixon-Coles should change the 0-0 probability vs pure Poisson."""
        dc = DixonColesModel(rho=-0.13)
        poisson = PoissonScoreModel()

        dc_probs = dc.predict_probabilities(EQUAL_A, EQUAL_B)
        po_probs = poisson.predict_probabilities(EQUAL_A, EQUAL_B)

        # With rho=-0.13 and equal teams, 0-0 weight is boosted → draw should increase
        assert abs(dc_probs["draw"] - po_probs["draw"]) > 0.001

    def test_wdl_sum_to_one(self) -> None:
        dc = DixonColesModel()
        probs = dc.predict_probabilities(STRONG, WEAK)
        total = probs["team_a_win"] + probs["draw"] + probs["team_b_win"]
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_wdl_sum_to_one_equal_teams(self) -> None:
        dc = DixonColesModel()
        probs = dc.predict_probabilities(EQUAL_A, EQUAL_B)
        total = probs["team_a_win"] + probs["draw"] + probs["team_b_win"]
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_strong_team_has_higher_win_probability(self) -> None:
        dc = DixonColesModel()
        probs = dc.predict_probabilities(STRONG, WEAK)
        assert probs["team_a_win"] > probs["team_b_win"]


class TestDixonColesSimulation:
    def test_deterministic_with_fixed_seed(self) -> None:
        dc = DixonColesModel()
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        result1 = dc.simulate_result(STRONG, WEAK, rng1)
        result2 = dc.simulate_result(STRONG, WEAK, rng2)
        assert result1.team_a_goals == result2.team_a_goals
        assert result1.team_b_goals == result2.team_b_goals

    def test_simulate_returns_non_negative_goals(self) -> None:
        dc = DixonColesModel()
        rng = np.random.default_rng(0)
        for _ in range(50):
            result = dc.simulate_result(EQUAL_A, EQUAL_B, rng)
            assert result.team_a_goals >= 0
            assert result.team_b_goals >= 0

    def test_different_seeds_can_produce_different_results(self) -> None:
        dc = DixonColesModel()
        results = set()
        for seed in range(20):
            rng = np.random.default_rng(seed)
            r = dc.simulate_result(EQUAL_A, EQUAL_B, rng)
            results.add((r.team_a_goals, r.team_b_goals))
        assert len(results) > 1

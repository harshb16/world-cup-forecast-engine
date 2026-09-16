"""Tests for GBMMatchModel."""

from __future__ import annotations

import pickle
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from app.models.domain import Team


def _make_team(team_id: str, rating: float, group_id: str = "A") -> Team:
    return Team(id=team_id, name=team_id, rating=rating, group_id=group_id)


STRONG = _make_team("strong", 1900.0)
WEAK = _make_team("weak", 1400.0)
EQUAL_A = _make_team("equal_a", 1600.0)
EQUAL_B = _make_team("equal_b", 1600.0)


def _make_mock_model(probs: list[float] | None = None) -> MagicMock:
    """Build a mock sklearn model that returns predictable probabilities."""
    probs = probs or [0.50, 0.25, 0.25]
    mock_model = MagicMock()
    mock_model.predict_proba.return_value = [probs]
    mock_model.classes_ = [0, 1, 2]
    return mock_model


def _make_mock_payload(probs: list[float] | None = None) -> dict:
    return {
        "model": _make_mock_model(probs),
        "feature_names": ["rating_diff", "rating_a", "rating_b", "abs_rating_diff"],
    }


class TestGBMMatchModelWithMock:
    def test_predict_probabilities_returns_valid_distribution(self) -> None:
        """predict_probabilities should return W/D/L summing to ~1."""
        with patch("app.simulation.ml_model.joblib.load") as mock_load, \
             patch("pathlib.Path.exists", return_value=True):
            mock_load.return_value = _make_mock_payload([0.50, 0.25, 0.25])
            from app.simulation.ml_model import GBMMatchModel
            model = GBMMatchModel(model_path=Path("/fake/path.pkl"))

        probs = model.predict_probabilities(STRONG, WEAK)
        total = probs["team_a_win"] + probs["draw"] + probs["team_b_win"]
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_predict_probabilities_maps_classes_correctly(self) -> None:
        with patch("app.simulation.ml_model.joblib.load") as mock_load, \
             patch("pathlib.Path.exists", return_value=True):
            mock_load.return_value = _make_mock_payload([0.60, 0.20, 0.20])
            from app.simulation.ml_model import GBMMatchModel
            model = GBMMatchModel(model_path=Path("/fake/path.pkl"))

        probs = model.predict_probabilities(STRONG, WEAK)
        assert probs["team_a_win"] == pytest.approx(0.60)
        assert probs["draw"] == pytest.approx(0.20)
        assert probs["team_b_win"] == pytest.approx(0.20)

    def test_simulate_result_is_deterministic_with_fixed_seed(self) -> None:
        with patch("app.simulation.ml_model.joblib.load") as mock_load, \
             patch("pathlib.Path.exists", return_value=True):
            mock_load.return_value = _make_mock_payload([0.50, 0.25, 0.25])
            from app.simulation.ml_model import GBMMatchModel
            model = GBMMatchModel(model_path=Path("/fake/path.pkl"))

        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)
        result1 = model.simulate_result(STRONG, WEAK, rng1)
        result2 = model.simulate_result(STRONG, WEAK, rng2)
        assert result1.team_a_goals == result2.team_a_goals
        assert result1.team_b_goals == result2.team_b_goals

    def test_simulate_result_non_negative_goals(self) -> None:
        with patch("app.simulation.ml_model.joblib.load") as mock_load, \
             patch("pathlib.Path.exists", return_value=True):
            mock_load.return_value = _make_mock_payload([0.50, 0.25, 0.25])
            from app.simulation.ml_model import GBMMatchModel
            model = GBMMatchModel(model_path=Path("/fake/path.pkl"))

        rng = np.random.default_rng(0)
        for _ in range(30):
            result = model.simulate_result(EQUAL_A, EQUAL_B, rng)
            assert result.team_a_goals >= 0
            assert result.team_b_goals >= 0

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        from app.simulation.ml_model import GBMMatchModel
        missing = tmp_path / "does_not_exist.pkl"
        with pytest.raises(FileNotFoundError, match="Run `python scripts/train_gbm_model.py`"):
            GBMMatchModel(model_path=missing)


class TestGBMWithRealArtifact:
    """Tests that run only when the trained pkl artifact exists."""

    @pytest.fixture
    def model(self):
        repo_root = Path(__file__).resolve().parents[3]
        model_path = repo_root / "data" / "processed" / "gbm_model.pkl"
        if not model_path.exists():
            pytest.skip("gbm_model.pkl not found; run scripts/train_gbm_model.py")
        from app.simulation.ml_model import GBMMatchModel
        return GBMMatchModel(model_path=model_path)

    def test_predict_probabilities_sums_to_one(self, model) -> None:
        probs = model.predict_probabilities(STRONG, WEAK)
        total = probs["team_a_win"] + probs["draw"] + probs["team_b_win"]
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_predict_probabilities_all_non_negative(self, model) -> None:
        probs = model.predict_probabilities(STRONG, WEAK)
        assert probs["team_a_win"] >= 0
        assert probs["draw"] >= 0
        assert probs["team_b_win"] >= 0

    def test_strong_team_has_higher_win_prob(self, model) -> None:
        probs = model.predict_probabilities(STRONG, WEAK)
        assert probs["team_a_win"] > probs["team_b_win"]

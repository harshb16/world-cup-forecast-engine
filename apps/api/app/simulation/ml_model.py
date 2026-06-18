"""Gradient boosting match model for international fixtures."""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np

from app.models.domain import MatchResult, Team
from app.simulation.match_models import OracleV2Model

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_MODEL_PATH = REPO_ROOT / "data" / "processed" / "gbm_model.pkl"
FEATURE_NAMES = ["rating_diff", "rating_a", "rating_b", "abs_rating_diff"]


class GBMMatchModel:
    """Scikit-learn GBM classifier for win/draw/loss probabilities.

    Loads a pre-trained CalibratedClassifierCV(GradientBoostingClassifier)
    from data/processed/gbm_model.pkl. Raises FileNotFoundError if the
    model artifact is missing (run scripts/train_gbm_model.py first).
    """

    def __init__(self, model_path: Path | None = None) -> None:
        path = model_path or DEFAULT_MODEL_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"GBM model artifact not found at {path}. "
                "Run `python scripts/train_gbm_model.py` to generate it."
            )
        payload = joblib.load(path)
        self.model = payload["model"]
        self.feature_names = payload.get("feature_names", FEATURE_NAMES)
        self._oracle = OracleV2Model()

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        """Return W/D/L probabilities from the GBM classifier."""
        features = self._build_features(team_a, team_b)
        raw_probs = self.model.predict_proba([features])[0]
        class_order = list(self.model.classes_)
        mapping = {
            int(label): float(prob)
            for label, prob in zip(class_order, raw_probs, strict=False)
        }
        return {
            "team_a_win": mapping.get(0, 0.33),
            "draw": mapping.get(1, 0.33),
            "team_b_win": mapping.get(2, 0.34),
        }

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
    ) -> MatchResult:
        """Sample W/D/L from GBM probs, then use OracleV2 expected goals for score."""
        probs = self.predict_probabilities(team_a, team_b)
        outcome = rng.choice(
            ["team_a_win", "draw", "team_b_win"],
            p=[probs["team_a_win"], probs["draw"], probs["team_b_win"]],
        )

        mu, nu = self._oracle.expected_goals(team_a, team_b)

        if outcome == "draw":
            goals = int(round((mu + nu) / 2))
            return MatchResult(team_a_goals=goals, team_b_goals=goals)
        if outcome == "team_a_win":
            team_a_goals = max(1, int(rng.poisson(mu)))
            team_b_goals = max(0, min(team_a_goals - 1, int(rng.poisson(nu))))
            return MatchResult(team_a_goals=team_a_goals, team_b_goals=team_b_goals)
        team_b_goals = max(1, int(rng.poisson(nu)))
        team_a_goals = max(0, min(team_b_goals - 1, int(rng.poisson(mu))))
        return MatchResult(team_a_goals=team_a_goals, team_b_goals=team_b_goals)

    def _build_features(self, team_a: Team, team_b: Team) -> list[float]:
        diff = team_a.rating - team_b.rating
        return [diff, team_a.rating, team_b.rating, abs(diff)]

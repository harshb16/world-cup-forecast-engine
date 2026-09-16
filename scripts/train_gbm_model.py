"""Train GBM match model using real match results + synthetic Forecast v2 data."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import GradientBoostingClassifier

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
FEATURE_NAMES = ["rating_diff", "rating_a", "rating_b", "abs_rating_diff"]


def _oracle_v2_probs(rating_a: float, rating_b: float) -> list[float]:
    """Compute win/draw/loss probabilities using Forecast v2 Poisson logic."""
    base = 1.28
    gap = (rating_a - rating_b) / 400.0
    mu = base * math.exp(gap * 0.42)
    nu = base * math.exp(-gap * 0.42)
    mu = min(max(mu, 0.25), 3.4)
    nu = min(max(nu, 0.25), 3.4)

    max_goals = 8
    team_a_win = 0.0
    draw = 0.0
    team_b_win = 0.0

    for x in range(max_goals + 1):
        px = (mu**x) * math.exp(-mu) / math.factorial(x)
        for y in range(max_goals + 1):
            py = (nu**y) * math.exp(-nu) / math.factorial(y)
            p = px * py
            if x > y:
                team_a_win += p
            elif x < y:
                team_b_win += p
            else:
                draw += p

    total = team_a_win + draw + team_b_win
    return [team_a_win / total, draw / total, team_b_win / total]


def _build_features(rating_a: float, rating_b: float) -> list[float]:
    diff = rating_a - rating_b
    return [diff, rating_a, rating_b, abs(diff)]


def _load_real_data() -> tuple[list[list[float]], list[int]]:
    """Load completed match results and convert to feature/label rows."""
    teams_path = PROCESSED_DIR / "teams.json"
    results_path = PROCESSED_DIR / "results.json"

    teams_raw = json.loads(teams_path.read_text(encoding="utf-8"))
    results_raw = json.loads(results_path.read_text(encoding="utf-8"))

    ratings: dict[str, float] = {}
    for team in teams_raw:
        ratings[team["id"]] = float(team.get("rating", 1500.0))

    features: list[list[float]] = []
    labels: list[int] = []

    for result in results_raw:
        team_a_id = result.get("team_a_id", "")
        team_b_id = result.get("team_b_id", "")
        team_a_goals = result.get("team_a_goals")
        team_b_goals = result.get("team_b_goals")

        if team_a_goals is None or team_b_goals is None:
            continue
        if team_a_id not in ratings or team_b_id not in ratings:
            continue

        ra = ratings[team_a_id]
        rb = ratings[team_b_id]
        feat = _build_features(ra, rb)
        features.append(feat)

        if team_a_goals > team_b_goals:
            labels.append(0)
        elif team_a_goals == team_b_goals:
            labels.append(1)
        else:
            labels.append(2)

    return features, labels


def _generate_synthetic_data(
    n_samples: int = 500, seed: int = 42
) -> tuple[list[list[float]], list[int]]:
    """Generate synthetic training pairs using Forecast v2 probabilities as ground truth."""
    rng = np.random.default_rng(seed)

    # Use a spread of ratings from plausible tournament range
    min_rating, max_rating = 1300.0, 2050.0
    ratings_a = rng.uniform(min_rating, max_rating, n_samples)
    ratings_b = rng.uniform(min_rating, max_rating, n_samples)

    features: list[list[float]] = []
    labels: list[int] = []

    for ra, rb in zip(ratings_a, ratings_b):
        probs = _oracle_v2_probs(float(ra), float(rb))
        label = int(rng.choice([0, 1, 2], p=probs))
        features.append(_build_features(float(ra), float(rb)))
        labels.append(label)

    return features, labels


def main() -> None:
    print("Loading real match data…")
    real_features, real_labels = _load_real_data()
    print(f"  Real matches loaded: {len(real_labels)}")

    print("Generating synthetic training data…")
    syn_features, syn_labels = _generate_synthetic_data(n_samples=500, seed=42)
    print(f"  Synthetic samples: {len(syn_labels)}")

    all_features = real_features + syn_features
    all_labels = real_labels + syn_labels
    print(f"  Total training samples: {len(all_labels)}")

    base_clf = GradientBoostingClassifier(
        n_estimators=50,
        max_depth=3,
        random_state=42,
    )
    model = CalibratedClassifierCV(base_clf, cv=3, method="sigmoid")

    print("Training model…")
    model.fit(all_features, all_labels)
    print("  Training complete.")

    output_path = PROCESSED_DIR / "gbm_model.pkl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": model, "feature_names": FEATURE_NAMES},
        output_path,
    )
    print(f"  Model saved to {output_path}")

    # Feature importance from the base estimator
    importances: dict[str, float] = {}
    for calibrated_clf in model.calibrated_classifiers_:
        base = calibrated_clf.estimator
        for name, imp in zip(FEATURE_NAMES, base.feature_importances_, strict=False):
            importances[name] = importances.get(name, 0.0) + float(imp)
    n_folds = len(model.calibrated_classifiers_)
    importances = {k: v / n_folds for k, v in importances.items()}

    importance_path = PROCESSED_DIR / "gbm_feature_importance.json"
    importance_path.write_text(
        json.dumps(importances, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"  Feature importances saved to {importance_path}")
    print("Done.")


if __name__ == "__main__":
    main()

"""Compatibility helpers for operator-managed data synchronization."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.models.schemas import SyncResponse
from app.services.results_sync_service import sync_results
from app.services.world_cup_schedule import group_matchday_for_date

REPO_ROOT = Path(__file__).resolve().parents[4]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"


def run_data_sync() -> SyncResponse:
    """Refresh match results without retraining unrelated model artifacts."""
    return sync_results()


def _current_matchday() -> int:
    return group_matchday_for_date(datetime.now(tz=UTC).date()) or 1


def _append_probability_snapshot(timestamp: str) -> None:
    """Append champion probabilities after a successful sync."""
    try:
        from app.core.config import DEFAULT_MODEL_TYPE
        from app.models.schemas import SimulateRequest
        from app.services.simulation_service import run_simulation

        summary = run_simulation(
            SimulateRequest(
                n_simulations=500,
                model_type=DEFAULT_MODEL_TYPE,
                seed=42,
            ),
            "processed",
        )
        history_path = PROCESSED_DIR / "probability_history.json"
        history: list[dict] = []
        if history_path.exists():
            history = json.loads(history_path.read_text(encoding="utf-8"))
        history.append(
            {
                "timestamp": timestamp,
                "matchday": _current_matchday(),
                "champion_probabilities": summary.champion_probabilities,
            }
        )
        history_path.write_text(
            json.dumps(history, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except Exception:
        return

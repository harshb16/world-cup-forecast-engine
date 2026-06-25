"""Build and serve a shared forecast snapshot for read-heavy UI pages."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.schemas import (
    ForecastSnapshotResponse,
    SimulateRequest,
)
from app.services.analytics_service import (
    calculate_group_chaos_from_summary,
    calculate_upset_radar,
)
from app.services.simulation_service import run_simulation

REPO_ROOT = Path(__file__).resolve().parents[4]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
SNAPSHOT_PATH = PROCESSED_DIR / "forecast_snapshot.json"
SNAPSHOT_SIMULATIONS = 5_000
SNAPSHOT_SEED = 42


def build_forecast_snapshot(
    data_mode: str = "processed",
) -> ForecastSnapshotResponse:
    """Run one simulation bank and derive all dashboard forecast artifacts."""
    summary = run_simulation(
        SimulateRequest(
            n_simulations=SNAPSHOT_SIMULATIONS,
            model_type=DEFAULT_MODEL_TYPE,
            seed=SNAPSHOT_SEED,
        ),
        data_mode,
    )
    group_chaos = calculate_group_chaos_from_summary(
        summary,
        data_mode,
        DEFAULT_MODEL_TYPE,
    )
    upsets = calculate_upset_radar(data_mode, DEFAULT_MODEL_TYPE, limit=6)
    return ForecastSnapshotResponse(
        generated_at=datetime.now(tz=UTC).replace(microsecond=0).isoformat(),
        summary=summary,
        group_chaos=group_chaos,
        upsets=upsets,
    )


def publish_forecast_snapshot(
    data_mode: str = "processed",
) -> ForecastSnapshotResponse:
    """Build then atomically publish a forecast snapshot."""
    snapshot = build_forecast_snapshot(data_mode)
    payload = json.dumps(
        snapshot.model_dump(mode="json"),
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
    ) + "\n"
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix=".forecast-snapshot-",
        suffix=".json",
        dir=SNAPSHOT_PATH.parent,
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        temporary_file.write(payload)
    temporary_path.chmod(0o644)
    os.replace(temporary_path, SNAPSHOT_PATH)
    return snapshot


def load_forecast_snapshot() -> ForecastSnapshotResponse:
    """Load the published snapshot without running Monte Carlo work."""
    if not SNAPSHOT_PATH.exists():
        raise FileNotFoundError(
            "Forecast snapshot is missing. Run result sync or publish it explicitly."
        )
    payload = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return ForecastSnapshotResponse.model_validate(payload)

"""Build and serve a shared forecast snapshot for read-heavy UI pages."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.schemas import (
    BracketSimulateRequest,
    ForecastSnapshotResponse,
    ForecastStatusResponse,
    SimulateRequest,
)
from app.services.analytics_service import (
    calculate_group_chaos_from_summary,
    calculate_upset_radar,
)
from app.services.bracket_service import run_bracket_simulation
from app.services.simulation_service import run_simulation
from app.services.third_place_tracker_service import calculate_third_place_tracker

REPO_ROOT = Path(__file__).resolve().parents[4]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
SNAPSHOT_PATH = PROCESSED_DIR / "forecast_snapshot.json"
SNAPSHOT_SIMULATIONS = 5_000
SNAPSHOT_SEED = 42


def build_snapshot_id(
    *,
    data_version: str | None,
    generated_at: str,
    model_type: str,
    n_simulations: int,
) -> str:
    """Return a stable identifier for one published forecast snapshot."""
    return f"{data_version or 'unknown'}:{generated_at}:{model_type}:{n_simulations}"


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
    third_place = calculate_third_place_tracker(
        data_mode,
        DEFAULT_MODEL_TYPE,
        n_simulations=SNAPSHOT_SIMULATIONS,
        seed=SNAPSHOT_SEED,
    )
    bracket = run_bracket_simulation(
        BracketSimulateRequest(
            model_type=DEFAULT_MODEL_TYPE,
            simulation_mode="favorite",
            seed=SNAPSHOT_SEED,
        ),
        data_mode,
    )
    featured_final = bracket.rounds["Final"][0]
    generated_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat()
    snapshot_id = build_snapshot_id(
        data_version=summary.metadata.data_version,
        generated_at=generated_at,
        model_type=summary.metadata.model_type,
        n_simulations=summary.metadata.n_simulations,
    )
    return ForecastSnapshotResponse(
        snapshot_id=snapshot_id,
        generated_at=generated_at,
        summary=summary,
        group_chaos=group_chaos,
        upsets=upsets,
        third_place=third_place,
        featured_final=featured_final,
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
    if "snapshot_id" not in payload:
        metadata = payload.get("summary", {}).get("metadata", {})
        payload["snapshot_id"] = build_snapshot_id(
            data_version=metadata.get("data_version"),
            generated_at=payload.get("generated_at", ""),
            model_type=metadata.get("model_type", DEFAULT_MODEL_TYPE),
            n_simulations=metadata.get("n_simulations", SNAPSHOT_SIMULATIONS),
        )
    return ForecastSnapshotResponse.model_validate(payload)


def load_forecast_status() -> ForecastStatusResponse:
    """Return lightweight forecast freshness metadata for polling clients."""
    snapshot = load_forecast_snapshot()
    metadata = snapshot.summary.metadata
    return ForecastStatusResponse(
        snapshot_id=snapshot.snapshot_id,
        data_version=metadata.data_version,
        forecast_generated_at=snapshot.generated_at,
        data_updated_at=metadata.last_updated,
        completed_result_count=metadata.completed_result_count,
        model_type=metadata.model_type,
        n_simulations=metadata.n_simulations,
    )

"""Build and serve a shared forecast snapshot for read-heavy UI pages."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import BOOTSTRAP_PROCESSED_DIR, DEFAULT_MODEL_TYPE
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
from app.services.runtime_store import (
    get_active_forecast_payload_path,
    publish_forecast_snapshot_record,
)
from app.services.simulation_service import run_simulation
from app.services.third_place_tracker_service import calculate_third_place_tracker

BOOTSTRAP_SNAPSHOT_PATH = BOOTSTRAP_PROCESSED_DIR / "forecast_snapshot.json"
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


def _resolve_snapshot_path() -> Path:
    active_path = get_active_forecast_payload_path()
    if active_path is not None and active_path.exists():
        return active_path
    return BOOTSTRAP_SNAPSHOT_PATH


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
    from app.services.simulation_bank_service import (
        build_simulation_bank,
        champion_probabilities_from_bank,
    )

    snapshot = build_forecast_snapshot(data_mode)
    metadata = snapshot.summary.metadata
    bank_path, bank_meta = build_simulation_bank(
        data_mode=data_mode,
        model_type=metadata.model_type,
        data_version=metadata.data_version,
    )
    bank_simulations = int(bank_meta["n_simulations"])
    champion_probabilities = champion_probabilities_from_bank(bank_path)
    generated_at = snapshot.generated_at
    snapshot_id = build_snapshot_id(
        data_version=metadata.data_version,
        generated_at=generated_at,
        model_type=metadata.model_type,
        n_simulations=bank_simulations,
    )
    payload = snapshot.model_dump(mode="json")
    payload["snapshot_id"] = snapshot_id
    payload["summary"]["champion_probabilities"] = champion_probabilities
    payload["summary"]["metadata"]["n_simulations"] = bank_simulations
    publish_forecast_snapshot_record(
        snapshot_id=snapshot_id,
        payload=payload,
        bank_path=bank_path,
    )
    return ForecastSnapshotResponse.model_validate(payload)


def load_forecast_snapshot() -> ForecastSnapshotResponse:
    """Load the published snapshot without running Monte Carlo work."""
    snapshot_path = _resolve_snapshot_path()
    if not snapshot_path.exists():
        raise FileNotFoundError(
            "Forecast snapshot is missing. Run result sync or publish it explicitly."
        )
    payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
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

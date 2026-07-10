"""Build and serve a shared forecast snapshot for read-heavy UI pages."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.archive_config import (
    get_archive_data_dir,
    is_archive_mode_active,
    resolve_archive_bank_path,
)
from app.core.config import BOOTSTRAP_PROCESSED_DIR, DEFAULT_MODEL_TYPE
from app.models.schemas import (
    ForecastSnapshotResponse,
    ForecastStatusResponse,
)
from app.models.domain import TournamentConfig
from app.services.analytics_service import (
    calculate_group_chaos_from_summary,
    calculate_upset_radar,
)
from app.services.bracket_service import plurality_bracket_from_bank
from app.services.data_loader import load_metadata, load_tournament
from app.services.runtime_store import (
    get_active_forecast_payload_path,
    publish_forecast_snapshot_record,
)
from app.services.snapshot_outlook_service import (
    build_champion_uncertainty,
    build_upcoming_fixture_outlook,
)

BOOTSTRAP_SNAPSHOT_PATH = BOOTSTRAP_PROCESSED_DIR / "forecast_snapshot.json"


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
    archive_dir = get_archive_data_dir()
    if archive_dir is not None:
        return archive_dir / "forecast_snapshot.json"
    active_path = get_active_forecast_payload_path()
    if active_path is not None and active_path.exists():
        return active_path
    return BOOTSTRAP_PROCESSED_DIR / "forecast_snapshot.json"


def resolve_forecast_bank_path() -> Path | None:
    """Return active simulation bank, including frozen archive bundles."""
    archive_bank = resolve_archive_bank_path()
    if archive_bank is not None:
        return archive_bank
    from app.services.runtime_store import get_active_forecast_bank_path

    return get_active_forecast_bank_path()


def build_forecast_snapshot_from_bank(
    bank_path: Path,
    bank_meta: dict[str, object],
    data_mode: str = "processed",
    config: TournamentConfig | None = None,
    generated_at: str | None = None,
) -> ForecastSnapshotResponse:
    """Derive all dashboard forecast artifacts from one simulation bank."""
    from app.services.simulation_bank_service import (
        simulation_summary_response_from_bank,
        third_place_tracker_from_bank,
    )

    model_type = str(bank_meta["model_version"])
    n_simulations = int(bank_meta["n_simulations"])
    master_seed = int(bank_meta["master_seed"])

    summary = simulation_summary_response_from_bank(
        bank_path,
        data_mode=data_mode,
        model_type=model_type,  # type: ignore[arg-type]
        seed=master_seed,
        config=config,
    )
    third_place = third_place_tracker_from_bank(
        bank_path, data_mode, model_type, config=config
    )  # type: ignore[arg-type]
    group_chaos = calculate_group_chaos_from_summary(
        summary,
        data_mode,
        model_type,  # type: ignore[arg-type]
        config=config,
    )
    upsets = calculate_upset_radar(
        data_mode, model_type, limit=6, config=config
    )  # type: ignore[arg-type]
    bracket = plurality_bracket_from_bank(bank_path, bank_meta, data_mode, config=config)
    featured_final = bracket.rounds["Final"][0]
    config = config or load_tournament(data_mode)
    upcoming_fixtures = build_upcoming_fixture_outlook(
        config,
        data_mode=data_mode,
        model_type=model_type,  # type: ignore[arg-type]
    )
    uncertainty = build_champion_uncertainty(
        summary.champion_probabilities,
        n_simulations=n_simulations,
    )
    generated_at = generated_at or datetime.now(tz=UTC).replace(microsecond=0).isoformat()
    snapshot_id = build_snapshot_id(
        data_version=summary.metadata.data_version,
        generated_at=generated_at,
        model_type=summary.metadata.model_type,
        n_simulations=n_simulations,
    )
    return ForecastSnapshotResponse(
        snapshot_id=snapshot_id,
        generated_at=generated_at,
        model_version=summary.metadata.model_type,
        summary=summary,
        group_chaos=group_chaos,
        upsets=upsets,
        third_place=third_place,
        bracket=bracket,
        featured_final=featured_final,
        upcoming_fixtures=upcoming_fixtures,
        uncertainty=uncertainty,
    )


def publish_forecast_snapshot(
    data_mode: str = "processed",
) -> ForecastSnapshotResponse:
    """Build then atomically publish a forecast snapshot."""
    from app.services.simulation_bank_service import build_simulation_bank
    from app.services.team_path_service import (
        TEAM_PATHS_FILENAME,
        all_team_paths_from_bank,
        serialize_team_paths,
    )

    metadata = load_metadata(data_mode)
    bank_path, bank_meta = build_simulation_bank(
        data_mode=data_mode,
        model_type=DEFAULT_MODEL_TYPE,
        data_version=metadata.get("data_version"),
    )
    snapshot = build_forecast_snapshot_from_bank(bank_path, bank_meta, data_mode)
    team_paths = all_team_paths_from_bank(
        bank_path,
        data_mode,
        model_type=str(bank_meta["model_version"]),
        seed=int(bank_meta["master_seed"]),
    )
    publish_forecast_snapshot_record(
        snapshot_id=snapshot.snapshot_id,
        payload=snapshot.model_dump(mode="json"),
        bank_path=bank_path,
        json_sidecars={TEAM_PATHS_FILENAME: serialize_team_paths(team_paths)},
    )
    return snapshot


def _candidate_snapshot_paths() -> list[Path]:
    paths: list[Path] = []
    active = get_active_forecast_payload_path()
    if active is not None and active.exists():
        paths.append(active)
    if BOOTSTRAP_SNAPSHOT_PATH.exists() and BOOTSTRAP_SNAPSHOT_PATH not in paths:
        paths.append(BOOTSTRAP_SNAPSHOT_PATH)
    return paths


def _enrich_snapshot_payload(payload: dict) -> dict:
    if "snapshot_id" not in payload:
        metadata = payload.get("summary", {}).get("metadata", {})
        payload["snapshot_id"] = build_snapshot_id(
            data_version=metadata.get("data_version"),
            generated_at=payload.get("generated_at", ""),
            model_type=metadata.get("model_type", DEFAULT_MODEL_TYPE),
            n_simulations=int(metadata.get("n_simulations", 0)),
        )
    if "model_version" not in payload:
        payload["model_version"] = payload.get("summary", {}).get("metadata", {}).get(
            "model_type",
            DEFAULT_MODEL_TYPE,
        )
    if "uncertainty" not in payload:
        summary = payload.get("summary", {})
        payload["uncertainty"] = build_champion_uncertainty(
            summary.get("champion_probabilities", {}),
            n_simulations=int(summary.get("metadata", {}).get("n_simulations", 0)),
        ).model_dump(mode="json")
    if "upcoming_fixtures" not in payload:
        payload["upcoming_fixtures"] = []
    return payload


def load_forecast_snapshot() -> ForecastSnapshotResponse:
    """Load the published snapshot without running Monte Carlo work."""
    from pydantic import ValidationError

    errors: list[Exception] = []
    for snapshot_path in _candidate_snapshot_paths():
        try:
            payload = _enrich_snapshot_payload(
                json.loads(snapshot_path.read_text(encoding="utf-8"))
            )
            return ForecastSnapshotResponse.model_validate(payload)
        except ValidationError as exc:
            errors.append(exc)
            continue

    if errors:
        raise errors[-1]
    raise FileNotFoundError(
        "Forecast snapshot is missing. Run result sync or publish it explicitly."
    )


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

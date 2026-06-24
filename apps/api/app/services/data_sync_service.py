"""Run ingest scripts to refresh processed tournament data."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.models.schemas import SyncResponse
from app.services.data_quality_service import build_data_quality_payload

REPO_ROOT = Path(__file__).resolve().parents[4]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
PYTHON = sys.executable

SYNC_SCRIPTS = (
    Path("scripts/ingest/fetch_worldcup_fifa.py"),
    Path("scripts/ingest/fetch_historical_results.py"),
    Path("scripts/ingest/validate_processed_data.py"),
    Path("scripts/train_gbm_model.py"),
)


def run_data_sync() -> SyncResponse:
    """Re-run ingest scripts and refresh derived processed artifacts."""
    errors: list[str] = []
    sync_timestamp = datetime.now(tz=UTC).isoformat()

    for relative_path in SYNC_SCRIPTS:
        script_path = REPO_ROOT / relative_path
        script_name = relative_path.as_posix()
        if not script_path.exists():
            errors.append(f"missing ingest script: {script_name}")
            continue

        result = subprocess.run(
            [PYTHON, str(script_path)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "").strip()
            errors.append(
                f"{script_name} failed: {message or f'exit code {result.returncode}'}"
            )

    if not errors:
        _refresh_metadata_timestamp(sync_timestamp)
        _refresh_data_quality_report()
        _append_probability_snapshot(sync_timestamp)

    metadata_path = PROCESSED_DIR / "metadata.json"
    last_updated = sync_timestamp
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        last_updated = str(metadata.get("last_updated") or sync_timestamp)

    return SyncResponse(
        success=len(errors) == 0,
        last_updated=last_updated,
        errors=errors,
    )


def _refresh_metadata_timestamp(timestamp: str) -> None:
    metadata_path = PROCESSED_DIR / "metadata.json"
    if not metadata_path.exists():
        return

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["last_updated"] = timestamp
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _refresh_data_quality_report() -> None:
    payload = build_data_quality_payload("processed")
    quality_path = PROCESSED_DIR / "data_quality.json"
    quality_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _current_matchday() -> int:
    fixtures_path = PROCESSED_DIR / "fixtures.json"
    if not fixtures_path.exists():
        return 1
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    played = sum(
        1
        for fixture in fixtures
        if (fixture.get("result") or {}).get("played")
    )
    return max(1, (played // 24) + 1)


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

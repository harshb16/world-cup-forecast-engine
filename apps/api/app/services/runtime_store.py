"""SQLite-backed runtime storage for tournament data and forecast snapshots."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from app.core.archive_config import get_archive_data_dir
from app.models.schemas import SyncJobDetailResponse, SyncResponse

REPO_ROOT = Path(__file__).resolve().parents[4]
BOOTSTRAP_PROCESSED_DIR = REPO_ROOT / "data" / "processed"
SYNC_FILES = ("fixtures.json", "results.json", "metadata.json", "data_quality.json")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS data_snapshots (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    directory TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS forecast_snapshots (
    id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    payload_path TEXT NOT NULL,
    bank_path TEXT,
    is_active INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    stage TEXT NOT NULL,
    created_at TEXT NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    provider TEXT,
    completed_result_count INTEGER,
    changed_fixture_count INTEGER,
    conflicts_json TEXT NOT NULL DEFAULT '[]',
    errors_json TEXT NOT NULL DEFAULT '[]',
    result_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_data_snapshots_active
    ON data_snapshots(is_active);
CREATE INDEX IF NOT EXISTS idx_forecast_snapshots_active
    ON forecast_snapshots(is_active);
"""


def get_runtime_root() -> Path:
    """Return writable runtime data root."""
    configured = os.getenv("WCO_RUNTIME_DATA_DIR")
    root = Path(configured) if configured else REPO_ROOT / "data" / "runtime"
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_database_path() -> Path:
    return get_runtime_root() / "wco.db"


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(get_database_path())
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_runtime_store() -> None:
    """Create runtime tables if needed."""
    with _connect() as connection:
        connection.executescript(_SCHEMA)


def get_active_data_directory() -> Path | None:
    """Return active runtime data directory when one is published."""
    init_runtime_store()
    with _connect() as connection:
        row = connection.execute(
            "SELECT directory FROM data_snapshots WHERE is_active = 1 LIMIT 1"
        ).fetchone()
    if row is None:
        return None
    return Path(row["directory"])


def resolve_processed_data_directory() -> Path:
    """Return active runtime data dir or checked-in bootstrap seed."""
    archive_dir = get_archive_data_dir()
    if archive_dir is not None:
        return archive_dir
    return get_active_data_directory() or BOOTSTRAP_PROCESSED_DIR


def publish_data_snapshot(staged_dir: Path) -> str:
    """Atomically publish one validated data snapshot."""
    init_runtime_store()
    snapshot_id = uuid.uuid4().hex
    created_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat()
    target_dir = get_runtime_root() / "data" / snapshot_id
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(staged_dir, target_dir)

    with _connect() as connection:
        connection.execute(
            "UPDATE data_snapshots SET is_active = 0 WHERE is_active = 1"
        )
        connection.execute(
            """
            INSERT INTO data_snapshots (id, created_at, directory, is_active)
            VALUES (?, ?, ?, 1)
            """,
            (snapshot_id, created_at, str(target_dir)),
        )
    return snapshot_id


def rollback_data_snapshot(snapshot_id: str) -> None:
    """Activate a previously published data snapshot."""
    init_runtime_store()
    with _connect() as connection:
        row = connection.execute(
            "SELECT id FROM data_snapshots WHERE id = ?",
            (snapshot_id,),
        ).fetchone()
        if row is None:
            raise KeyError(snapshot_id)
        connection.execute("UPDATE data_snapshots SET is_active = 0")
        connection.execute(
            "UPDATE data_snapshots SET is_active = 1 WHERE id = ?",
            (snapshot_id,),
        )


def list_data_snapshots(limit: int = 10) -> list[dict[str, Any]]:
    init_runtime_store()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, is_active
            FROM data_snapshots
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def publish_forecast_snapshot_record(
    *,
    snapshot_id: str,
    payload: dict[str, Any],
    bank_path: Path | None = None,
    json_sidecars: dict[str, Any] | None = None,
) -> str:
    """Persist a complete forecast bundle, then mark it active."""
    init_runtime_store()
    record_id = uuid.uuid4().hex
    created_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat()
    target_dir = get_runtime_root() / "forecasts" / record_id
    target_dir.mkdir(parents=True, exist_ok=True)
    payload_path = target_dir / "forecast_snapshot.json"
    payload_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for filename, sidecar_payload in (json_sidecars or {}).items():
        if Path(filename).name != filename:
            raise ValueError(f"forecast sidecar must be a filename: {filename}")
        (target_dir / filename).write_text(
            json.dumps(
                sidecar_payload,
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    with _connect() as connection:
        connection.execute(
            "UPDATE forecast_snapshots SET is_active = 0 WHERE is_active = 1"
        )
        connection.execute(
            """
            INSERT INTO forecast_snapshots (
                id, snapshot_id, created_at, payload_path, bank_path, is_active
            ) VALUES (?, ?, ?, ?, ?, 1)
            """,
            (
                record_id,
                snapshot_id,
                created_at,
                str(payload_path),
                str(bank_path) if bank_path else None,
            ),
        )
    return record_id


def get_active_forecast_payload_path() -> Path | None:
    init_runtime_store()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT payload_path FROM forecast_snapshots
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    return Path(row["payload_path"])


def get_active_forecast_directory() -> Path | None:
    """Return the directory containing the active forecast snapshot payload."""
    payload_path = get_active_forecast_payload_path()
    if payload_path is None:
        return None
    return payload_path.parent


def get_active_forecast_bank_path() -> Path | None:
    """Return the simulation bank path for the active forecast snapshot."""
    init_runtime_store()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT bank_path FROM forecast_snapshots
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None or row["bank_path"] is None:
        return None
    return Path(row["bank_path"])


def rollback_forecast_snapshot(record_id: str) -> None:
    init_runtime_store()
    with _connect() as connection:
        row = connection.execute(
            "SELECT id FROM forecast_snapshots WHERE id = ?",
            (record_id,),
        ).fetchone()
        if row is None:
            raise KeyError(record_id)
        connection.execute("UPDATE forecast_snapshots SET is_active = 0")
        connection.execute(
            "UPDATE forecast_snapshots SET is_active = 1 WHERE id = ?",
            (record_id,),
        )


def list_forecast_snapshots(limit: int = 10) -> list[dict[str, Any]]:
    init_runtime_store()
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, snapshot_id, created_at, is_active, bank_path
            FROM forecast_snapshots
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_sync_job(record: dict[str, Any]) -> None:
    init_runtime_store()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO sync_jobs (
                job_id, status, stage, created_at, started_at, finished_at,
                provider, completed_result_count, changed_fixture_count,
                conflicts_json, errors_json, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                status = excluded.status,
                stage = excluded.stage,
                started_at = excluded.started_at,
                finished_at = excluded.finished_at,
                provider = excluded.provider,
                completed_result_count = excluded.completed_result_count,
                changed_fixture_count = excluded.changed_fixture_count,
                conflicts_json = excluded.conflicts_json,
                errors_json = excluded.errors_json,
                result_json = excluded.result_json
            """,
            (
                record["job_id"],
                record["status"],
                record["stage"],
                record["created_at"],
                record.get("started_at"),
                record.get("finished_at"),
                record.get("provider"),
                record.get("completed_result_count"),
                record.get("changed_fixture_count"),
                json.dumps(record.get("conflicts", [])),
                json.dumps(record.get("errors", [])),
                json.dumps(record["result"]) if record.get("result") else None,
            ),
        )


def get_latest_sync_job_record() -> dict[str, Any] | None:
    init_runtime_store()
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT * FROM sync_jobs
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    payload = dict(row)
    payload["conflicts"] = json.loads(payload.pop("conflicts_json") or "[]")
    payload["errors"] = json.loads(payload.pop("errors_json") or "[]")
    if payload.get("result_json"):
        payload["result"] = SyncResponse.model_validate_json(payload.pop("result_json"))
    else:
        payload.pop("result_json", None)
        payload["result"] = None
    return payload


def get_sync_job_record(job_id: str) -> dict[str, Any] | None:
    init_runtime_store()
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM sync_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
    if row is None:
        return None
    payload = dict(row)
    payload["conflicts"] = json.loads(payload.pop("conflicts_json") or "[]")
    payload["errors"] = json.loads(payload.pop("errors_json") or "[]")
    if payload.get("result_json"):
        payload["result"] = SyncResponse.model_validate_json(payload.pop("result_json"))
    else:
        payload.pop("result_json", None)
        payload["result"] = None
    return payload


def reset_runtime_store_for_tests() -> None:
    """Delete runtime DB and files."""
    root = get_runtime_root()
    db_path = get_database_path()
    if db_path.exists():
        db_path.unlink()
    for subdir in ("data", "forecasts", "banks"):
        path = root / subdir
        if path.exists():
            shutil.rmtree(path)

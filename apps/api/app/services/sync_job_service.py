"""Async job orchestration for operator result sync."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.models.schemas import (
    SyncJobDetailResponse,
    SyncJobStage,
    SyncJobStartResponse,
    SyncJobState,
    SyncResponse,
)
from app.services.results_sync_service import sync_results
from app.services.runtime_store import get_sync_job_record, upsert_sync_job

MANUAL_SYNC_COOLDOWN_SECONDS = 60

_jobs_lock = threading.Lock()
_running = False
_last_manual_sync_at: datetime | None = None
_jobs: dict[str, SyncJobRecord] = {}


@dataclass
class SyncJobRecord:
    job_id: str
    status: SyncJobState
    stage: SyncJobStage
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    provider: str | None = None
    completed_result_count: int | None = None
    changed_fixture_count: int | None = None
    conflicts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    result: SyncResponse | None = None


class SyncJobCooldownError(RuntimeError):
    """Raised when manual sync is requested inside the cooldown window."""


class SyncJobAlreadyRunningError(RuntimeError):
    """Raised when another sync job is already active."""


def start_sync_job() -> SyncJobStartResponse:
    """Queue a background result-sync job."""
    global _last_manual_sync_at, _running

    now = datetime.now(tz=UTC)
    with _jobs_lock:
        if _running:
            raise SyncJobAlreadyRunningError("A result sync is already running.")
        if (
            _last_manual_sync_at is not None
            and (now - _last_manual_sync_at).total_seconds()
            < MANUAL_SYNC_COOLDOWN_SECONDS
        ):
            raise SyncJobCooldownError(
                f"Manual sync cooldown active ({MANUAL_SYNC_COOLDOWN_SECONDS}s)."
            )

        job_id = uuid.uuid4().hex
        created_at = now.replace(microsecond=0).isoformat()
        record = SyncJobRecord(
            job_id=job_id,
            status="queued",
            stage="queued",
            created_at=created_at,
        )
        _jobs[job_id] = record
        _last_manual_sync_at = now
        _running = True
        _persist_record(record)

    thread = threading.Thread(
        target=_execute_job,
        args=(job_id,),
        name=f"sync-job-{job_id[:8]}",
        daemon=True,
    )
    thread.start()
    return SyncJobStartResponse(job_id=job_id, status="queued")


def get_sync_job(job_id: str) -> SyncJobDetailResponse:
    """Return one sync job record."""
    with _jobs_lock:
        record = _jobs.get(job_id)
    if record is not None:
        return _to_response(record)

    stored = get_sync_job_record(job_id)
    if stored is None:
        raise KeyError(job_id)
    return SyncJobDetailResponse(
        job_id=stored["job_id"],
        status=stored["status"],
        stage=stored["stage"],
        created_at=stored["created_at"],
        started_at=stored.get("started_at"),
        finished_at=stored.get("finished_at"),
        provider=stored.get("provider"),
        completed_result_count=stored.get("completed_result_count"),
        changed_fixture_count=stored.get("changed_fixture_count"),
        conflicts=stored.get("conflicts", []),
        errors=stored.get("errors", []),
        result=stored.get("result"),
    )


def _execute_job(job_id: str) -> None:
    global _running

    def on_stage(stage: SyncJobStage, message: str | None = None) -> None:
        with _jobs_lock:
            record = _jobs.get(job_id)
            if record is None:
                return
            record.status = "running"
            record.stage = stage
            if record.started_at is None:
                record.started_at = datetime.now(tz=UTC).replace(
                    microsecond=0
                ).isoformat()
            if message and message not in record.conflicts:
                if stage == "compare" and "conflict" in message.lower():
                    record.conflicts.append(message)
            _persist_record(record)

    try:
        _update_job(job_id, status="running", stage="fetch")
        result = sync_results(on_stage=on_stage)
        finished_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat()
        with _jobs_lock:
            record = _jobs.get(job_id)
            if record is None:
                return
            record.finished_at = finished_at
            record.provider = result.provider
            record.completed_result_count = result.completed_result_count
            record.changed_fixture_count = result.changed_fixture_count
            record.errors = list(result.errors)
            if any("conflict" in error.lower() for error in result.errors):
                record.conflicts = [
                    error for error in result.errors if "conflict" in error.lower()
                ]
            record.result = result
            record.stage = "done"
            record.status = "succeeded" if result.success else "failed"
            _persist_record(record)
    except Exception as exc:  # pragma: no cover - defensive guardrail
        finished_at = datetime.now(tz=UTC).replace(microsecond=0).isoformat()
        with _jobs_lock:
            record = _jobs.get(job_id)
            if record is None:
                return
            record.finished_at = finished_at
            record.stage = "done"
            record.status = "failed"
            record.errors = [str(exc)]
            record.result = SyncResponse(
                success=False,
                last_updated=record.created_at,
                errors=[str(exc)],
            )
            _persist_record(record)
    finally:
        with _jobs_lock:
            _running = False


def _update_job(
    job_id: str,
    *,
    status: SyncJobState | None = None,
    stage: SyncJobStage | None = None,
) -> None:
    with _jobs_lock:
        record = _jobs.get(job_id)
        if record is None:
            return
        if status is not None:
            record.status = status
        if stage is not None:
            record.stage = stage
        if record.started_at is None and status == "running":
            record.started_at = datetime.now(tz=UTC).replace(
                microsecond=0
            ).isoformat()
        _persist_record(record)


def _record_payload(record: SyncJobRecord) -> dict[str, Any]:
    return {
        "job_id": record.job_id,
        "status": record.status,
        "stage": record.stage,
        "created_at": record.created_at,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "provider": record.provider,
        "completed_result_count": record.completed_result_count,
        "changed_fixture_count": record.changed_fixture_count,
        "conflicts": record.conflicts,
        "errors": record.errors,
        "result": record.result.model_dump(mode="json") if record.result else None,
    }


def _persist_record(record: SyncJobRecord) -> None:
    upsert_sync_job(_record_payload(record))


def _to_response(record: SyncJobRecord) -> SyncJobDetailResponse:
    return SyncJobDetailResponse(
        job_id=record.job_id,
        status=record.status,
        stage=record.stage,
        created_at=record.created_at,
        started_at=record.started_at,
        finished_at=record.finished_at,
        provider=record.provider,
        completed_result_count=record.completed_result_count,
        changed_fixture_count=record.changed_fixture_count,
        conflicts=record.conflicts,
        errors=record.errors,
        result=record.result,
    )


def reset_sync_job_state_for_tests() -> None:
    """Clear in-memory sync job state."""
    global _running, _last_manual_sync_at

    with _jobs_lock:
        _jobs.clear()
        _running = False
        _last_manual_sync_at = None

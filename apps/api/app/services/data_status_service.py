"""Aggregate provider freshness and sync scheduler state."""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Any

from app.core.archive_config import get_frozen_label, is_archive_mode_active
from app.core.config import get_data_mode
from app.models.schemas import (
    DataMetadataResponse,
    DataStatusResponse,
    ProviderStatusResponse,
    SyncJobDetailResponse,
)
from app.services.data_loader import get_processed_data_dir, load_metadata
from app.services.provider_status import normalize_match_status
from app.services.results_sync_service import admin_sync_is_configured
from app.services.runtime_store import get_latest_sync_job_record
from app.services.sync_scheduler_service import (
    ACTIVE_INTERVAL_MINUTES,
    IDLE_INTERVAL_MINUTES,
    is_tournament_active,
    recommended_interval_minutes,
)


def _match_status_counts() -> dict[str, int]:
    fixtures_path = get_processed_data_dir() / "fixtures.json"
    if not fixtures_path.exists():
        return {"scheduled": 0, "in_play": 0, "finished": 0}
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    counts: Counter[str] = Counter()
    for fixture in fixtures:
        if fixture.get("stage") != "group":
            continue
        status = normalize_match_status(fixture.get("status", "scheduled"))
        counts[status] += 1
    return {
        "scheduled": counts.get("scheduled", 0),
        "in_play": counts.get("in_play", 0),
        "finished": counts.get("finished", 0),
    }


def _provider_statuses(metadata: dict[str, Any]) -> list[ProviderStatusResponse]:
    token_configured = bool(os.getenv("FOOTBALL_DATA_API_TOKEN"))
    last_provider = metadata.get("result_source")
    last_updated = metadata.get("last_updated")
    return [
        ProviderStatusResponse(
            name="football-data.org",
            configured=token_configured,
            is_primary=token_configured,
            last_used=last_updated if last_provider == "football-data.org" else None,
        ),
        ProviderStatusResponse(
            name="FIFA API fallback",
            configured=True,
            is_primary=not token_configured,
            last_used=last_updated if last_provider == "FIFA API fallback" else None,
        ),
    ]


def build_data_status() -> DataStatusResponse:
    """Return operator-facing data freshness and scheduler state."""
    metadata = load_metadata(get_data_mode())
    latest_job_payload = get_latest_sync_job_record()
    latest_job = (
        SyncJobDetailResponse.model_validate(latest_job_payload)
        if latest_job_payload is not None
        else None
    )
    tournament_active = is_tournament_active()
    sync_disabled = is_archive_mode_active()
    return DataStatusResponse(
        metadata=DataMetadataResponse.model_validate(metadata),
        match_status_counts=_match_status_counts(),
        providers=_provider_statuses(metadata),
        tournament_active=tournament_active,
        scheduler_active_interval_minutes=ACTIVE_INTERVAL_MINUTES,
        scheduler_idle_interval_minutes=IDLE_INTERVAL_MINUTES,
        recommended_interval_minutes=recommended_interval_minutes(),
        admin_sync_configured=admin_sync_is_configured(),
        sync_disabled=sync_disabled,
        sync_disabled_reason=get_frozen_label() if sync_disabled else None,
        latest_job=latest_job,
    )

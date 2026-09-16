"""Tests for cron scheduler helpers."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from app.services.sync_scheduler_service import (
    is_tournament_active,
    recommended_interval_minutes,
    should_run_cron_sync,
)


def test_recommended_interval_is_shorter_when_tournament_active(
    tmp_path, monkeypatch
) -> None:
    fixtures = [
        {
            "stage": "group",
            "status": "in_play",
            "kickoff_utc": "2026-06-12T19:00:00Z",
        }
    ]
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "fixtures.json").write_text(json.dumps(fixtures))
    monkeypatch.setattr(
        "app.services.sync_scheduler_service.get_processed_data_dir",
        lambda: processed,
    )

    assert is_tournament_active(datetime(2026, 6, 12, 20, tzinfo=UTC)) is True
    assert recommended_interval_minutes(datetime(2026, 6, 12, 20, tzinfo=UTC)) == 5


def test_should_run_cron_sync_respects_idle_interval(tmp_path, monkeypatch) -> None:
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "fixtures.json").write_text(json.dumps([]))
    now = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    (processed / "metadata.json").write_text(
        json.dumps({"last_updated": (now - timedelta(minutes=10)).isoformat()})
    )
    monkeypatch.setattr(
        "app.services.sync_scheduler_service.get_processed_data_dir",
        lambda: processed,
    )

    assert should_run_cron_sync(now) is False

    (processed / "metadata.json").write_text(
        json.dumps({"last_updated": (now - timedelta(minutes=31)).isoformat()})
    )
    assert should_run_cron_sync(now) is True

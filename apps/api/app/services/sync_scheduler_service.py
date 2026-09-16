"""Cron scheduling helpers for automated result sync."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.services.data_loader import get_processed_data_dir
from app.services.provider_status import normalize_match_status

ACTIVE_INTERVAL_MINUTES = 5
IDLE_INTERVAL_MINUTES = 30
ACTIVE_WINDOW = timedelta(hours=3)


def is_tournament_active(now: datetime | None = None) -> bool:
    """Return whether fixtures are live or imminently kicking off."""
    moment = now or datetime.now(tz=UTC)
    fixtures_path = get_processed_data_dir() / "fixtures.json"
    if not fixtures_path.exists():
        return False
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    for fixture in fixtures:
        if fixture.get("stage") != "group":
            continue
        status = fixture.get("status", "scheduled")
        if status == "in_play":
            return True
        kickoff = fixture.get("kickoff_utc")
        if not isinstance(kickoff, str):
            continue
        try:
            kickoff_at = datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
        except ValueError:
            continue
        if status != "finished" and abs(moment - kickoff_at) <= ACTIVE_WINDOW:
            return True
    return False


def recommended_interval_minutes(now: datetime | None = None) -> int:
    return (
        ACTIVE_INTERVAL_MINUTES
        if is_tournament_active(now)
        else IDLE_INTERVAL_MINUTES
    )


def should_run_cron_sync(now: datetime | None = None) -> bool:
    """Return whether cron should trigger another sync now."""
    moment = now or datetime.now(tz=UTC)
    metadata_path = get_processed_data_dir() / "metadata.json"
    if not metadata_path.exists():
        return True
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    last_updated = metadata.get("last_updated")
    if not isinstance(last_updated, str) or not last_updated:
        return True
    try:
        updated_at = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
    except ValueError:
        return True
    interval = timedelta(minutes=recommended_interval_minutes(moment))
    return moment - updated_at >= interval


def run_cron_sync_if_due() -> tuple[bool, str]:
    """Run sync when the scheduler interval has elapsed."""
    if not should_run_cron_sync():
        return False, "skipped: interval not elapsed"
    if not os.getenv("WCO_ADMIN_SYNC_KEY"):
        return False, "skipped: WCO_ADMIN_SYNC_KEY is not configured"
    from app.services.results_sync_service import sync_results

    result = sync_results()
    if result.success:
        return True, f"synced via {result.provider}"
    return False, result.errors[0] if result.errors else "sync failed"


def main() -> int:
  import argparse

  parser = argparse.ArgumentParser(description="World Cup Forecast Engine cron result sync")
  parser.add_argument(
      "--cron",
      action="store_true",
      help="Run sync only when the active/idle interval has elapsed",
  )
  parser.add_argument(
      "--force",
      action="store_true",
      help="Run sync immediately, ignoring scheduler interval",
  )
  args = parser.parse_args()
  if args.force:
      if not os.getenv("WCO_ADMIN_SYNC_KEY"):
          print("skipped: WCO_ADMIN_SYNC_KEY is not configured")
          return 1
      from app.services.results_sync_service import sync_results

      result = sync_results()
      print("synced" if result.success else result.errors[0])
      return 0 if result.success else 1
  ran, message = run_cron_sync_if_due()
  print(message)
  return 0 if ran or message.startswith("skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())


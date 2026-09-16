"""Tests for SQLite-backed runtime storage."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from app.services.runtime_store import (
    BOOTSTRAP_PROCESSED_DIR,
    get_active_data_directory,
    get_active_forecast_directory,
    init_runtime_store,
    list_data_snapshots,
    publish_data_snapshot,
    publish_forecast_snapshot_record,
    reset_runtime_store_for_tests,
    resolve_processed_data_directory,
    rollback_data_snapshot,
)


@pytest.fixture
def runtime_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "runtime"
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(root))
    reset_runtime_store_for_tests()
    init_runtime_store()
    return root


def _stage_bootstrap_copy(tmp_path: Path, name: str = "staged") -> Path:
    staged = tmp_path / name
    if staged.exists():
        shutil.rmtree(staged)
    shutil.copytree(BOOTSTRAP_PROCESSED_DIR, staged)
    return staged


def test_publish_data_snapshot_switches_active_pointer(
    runtime_root: Path,
    tmp_path: Path,
) -> None:
    first_id = publish_data_snapshot(_stage_bootstrap_copy(tmp_path))
    first_dir = get_active_data_directory()
    assert first_dir is not None
    assert (first_dir / "fixtures.json").exists()

    staged = _stage_bootstrap_copy(tmp_path, "staged-second")
    fixtures = json.loads((staged / "fixtures.json").read_text())
    fixtures[0] = {
        **fixtures[0],
        "status": "finished",
    }
    (staged / "fixtures.json").write_text(json.dumps(fixtures))

    second_id = publish_data_snapshot(staged)
    second_dir = get_active_data_directory()

    assert first_id != second_id
    assert second_dir == first_dir.parent / second_id
    assert resolve_processed_data_directory() == second_dir
    snapshots = list_data_snapshots()
    assert sum(1 for row in snapshots if row["is_active"]) == 1


def test_rollback_data_snapshot_restores_prior_pointer(
    runtime_root: Path,
    tmp_path: Path,
) -> None:
    first_id = publish_data_snapshot(_stage_bootstrap_copy(tmp_path))
    first_dir = get_active_data_directory()
    publish_data_snapshot(_stage_bootstrap_copy(tmp_path, "staged-second"))
    assert get_active_data_directory() != first_dir

    rollback_data_snapshot(first_id)
    assert get_active_data_directory() == first_dir


def test_publish_forecast_snapshot_record_is_active(
    runtime_root: Path,
) -> None:
    record_id = publish_forecast_snapshot_record(
        snapshot_id="seed:now:calibrated_elo:5000",
        payload={"snapshot_id": "seed:now:calibrated_elo:5000", "generated_at": "now"},
        json_sidecars={"team_paths.json": {"teams": {"arg": {"team_id": "arg"}}}},
    )
    assert record_id
    forecast_dir = get_active_forecast_directory()
    assert forecast_dir is not None
    assert json.loads((forecast_dir / "team_paths.json").read_text()) == {
        "teams": {"arg": {"team_id": "arg"}}
    }

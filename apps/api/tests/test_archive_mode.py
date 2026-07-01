"""Tests for frozen tournament archive mode."""

from __future__ import annotations

import shutil

import pytest
from fastapi.testclient import TestClient

from app.core.archive_config import SUPPORTED_ARCHIVE_DIRS
from app.core.config import BOOTSTRAP_PROCESSED_DIR
from app.main import app
from app.services.data_loader import get_processed_data_dir, load_metadata


client = TestClient(app)


@pytest.fixture
def archive_dataset(tmp_path, monkeypatch):
    archive_dir = tmp_path / "wc2026"
    shutil.copytree(BOOTSTRAP_PROCESSED_DIR, archive_dir)
    monkeypatch.setitem(SUPPORTED_ARCHIVE_DIRS, "wc2026", archive_dir)
    monkeypatch.setenv("WCO_ARCHIVE_MODE", "wc2026")
    return archive_dir


def test_archive_mode_loads_processed_dataset(archive_dataset) -> None:
    assert get_processed_data_dir() == archive_dataset
    metadata = load_metadata("processed")
    assert metadata["is_frozen"] is True
    assert metadata["archive_mode"] == "wc2026"
    assert metadata["frozen_label"] == "Dataset frozen — Final, July 2026"


def test_metadata_endpoint_reports_frozen_state(archive_dataset) -> None:
    response = client.get("/metadata")
    assert response.status_code == 200
    payload = response.json()
    assert payload["is_frozen"] is True
    assert payload["archive_mode"] == "wc2026"


def test_sync_is_rejected_in_archive_mode(archive_dataset, monkeypatch) -> None:
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "correct-key")
    response = client.post(
        "/admin/sync/results",
        headers={"X-WCO-Admin-Key": "correct-key"},
    )
    assert response.status_code == 409
    assert "frozen" in response.json()["detail"].lower()


def test_data_status_reports_sync_disabled(archive_dataset) -> None:
    response = client.get("/data/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["sync_disabled"] is True
    assert payload["sync_disabled_reason"] == "Dataset frozen — Final, July 2026"

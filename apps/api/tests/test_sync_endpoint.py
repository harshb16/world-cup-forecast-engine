"""Tests for async admin result-sync jobs."""

import threading
import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import SyncResponse
from app.services import sync_job_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_sync_jobs() -> None:
    sync_job_service.reset_sync_job_state_for_tests()
    yield
    sync_job_service.reset_sync_job_state_for_tests()


def test_legacy_sync_endpoint_is_not_public() -> None:
    response = client.post("/sync")

    assert response.status_code == 404


def test_admin_sync_requires_configuration(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WCO_ADMIN_SYNC_KEY", raising=False)

    response = client.post("/admin/sync/results")

    assert response.status_code == 503


def test_admin_sync_rejects_invalid_key(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "correct-key")

    response = client.post(
        "/admin/sync/results",
        headers={"X-WCO-Admin-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_admin_sync_accepts_background_job(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "correct-key")
    expected = SyncResponse(
        success=True,
        last_updated="2026-06-25T12:00:00+00:00",
        provider="football-data.org",
        completed_result_count=54,
        changed_fixture_count=0,
    )

    with patch("app.services.sync_job_service.sync_results", return_value=expected):
        response = client.post(
            "/admin/sync/results",
            headers={"X-WCO-Admin-Key": "correct-key"},
        )

        assert response.status_code == 202
        job_id = response.json()["job_id"]
        assert response.json()["status"] == "queued"

        job = _wait_for_terminal_job(job_id, "correct-key")

    assert job["status"] == "succeeded"
    assert job["provider"] == "football-data.org"
    assert job["result"]["completed_result_count"] == 54


def test_admin_sync_job_lookup_requires_auth(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "correct-key")

    with patch(
        "app.services.sync_job_service.sync_results",
        return_value=SyncResponse(
            success=True,
            last_updated="2026-06-25T12:00:00+00:00",
        ),
    ):
        started = client.post(
            "/admin/sync/results",
            headers={"X-WCO-Admin-Key": "correct-key"},
        ).json()

    response = client.get(
        f"/admin/sync/{started['job_id']}",
        headers={"X-WCO-Admin-Key": "wrong-key"},
    )

    assert response.status_code == 401


def test_admin_sync_rejects_concurrent_job(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "correct-key")
    release = threading.Event()

    def slow_sync(*_args, **_kwargs) -> SyncResponse:
        release.wait(timeout=1)
        return SyncResponse(
            success=True,
            last_updated="2026-06-25T12:00:00+00:00",
        )

    with patch("app.services.sync_job_service.sync_results", side_effect=slow_sync):
        first = client.post(
            "/admin/sync/results",
            headers={"X-WCO-Admin-Key": "correct-key"},
        )
        second = client.post(
            "/admin/sync/results",
            headers={"X-WCO-Admin-Key": "correct-key"},
        )

        assert first.status_code == 202
        assert second.status_code == 409
        release.set()
        _wait_for_terminal_job(first.json()["job_id"], "correct-key")


def test_admin_sync_enforces_manual_cooldown(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("WCO_ADMIN_SYNC_KEY", "correct-key")

    with patch(
        "app.services.sync_job_service.sync_results",
        return_value=SyncResponse(
            success=True,
            last_updated="2026-06-25T12:00:00+00:00",
        ),
    ):
        first = client.post(
            "/admin/sync/results",
            headers={"X-WCO-Admin-Key": "correct-key"},
        )
        _wait_for_terminal_job(first.json()["job_id"], "correct-key")
        second = client.post(
            "/admin/sync/results",
            headers={"X-WCO-Admin-Key": "correct-key"},
        )

    assert first.status_code == 202
    assert second.status_code == 429


def _wait_for_terminal_job(job_id: str, admin_key: str) -> dict:
    for _ in range(100):
        response = client.get(
            f"/admin/sync/{job_id}",
            headers={"X-WCO-Admin-Key": admin_key},
        )
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"succeeded", "failed", "rejected"}:
            return payload
        time.sleep(0.02)
    raise AssertionError("sync job did not finish in time")

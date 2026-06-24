"""Tests for data sync API endpoint."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import SyncResponse


client = TestClient(app)


def test_sync_endpoint_returns_response_shape() -> None:
    with patch(
        "app.api.routes.run_data_sync",
        return_value=SyncResponse(
            success=True,
            last_updated="2026-06-18T12:00:00+00:00",
            errors=[],
        ),
    ):
        response = client.post("/sync")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["last_updated"] == "2026-06-18T12:00:00+00:00"
    assert payload["errors"] == []


def test_sync_endpoint_reports_errors() -> None:
    with patch(
        "app.api.routes.run_data_sync",
        return_value=SyncResponse(
            success=False,
            last_updated="2026-06-18T12:00:00+00:00",
            errors=["fetch_worldcup_fifa.py failed: blocked"],
        ),
    ):
        response = client.post("/sync")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is False
    assert len(payload["errors"]) == 1


def test_run_data_sync_collects_script_failures() -> None:
    from app.services.data_sync_service import run_data_sync

    with patch(
        "app.services.data_sync_service.subprocess.run",
        return_value=type(
            "Result",
            (),
            {"returncode": 1, "stdout": "", "stderr": "validation failed"},
        )(),
    ):
        with patch(
            "app.services.data_sync_service._refresh_metadata_timestamp"
        ) as refresh_metadata:
            with patch(
                "app.services.data_sync_service._refresh_data_quality_report"
            ) as refresh_quality:
                response = run_data_sync()

    assert response.success is False
    assert response.errors
    refresh_metadata.assert_not_called()
    refresh_quality.assert_not_called()


def test_sync_pipeline_retrains_gbm() -> None:
    from app.services.data_sync_service import SYNC_SCRIPTS

    assert SYNC_SCRIPTS[-1].as_posix() == "scripts/train_gbm_model.py"

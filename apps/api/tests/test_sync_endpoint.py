"""Tests for operator-managed data sync."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_sync_endpoint_is_not_public() -> None:
    response = client.post("/sync")

    assert response.status_code == 404


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

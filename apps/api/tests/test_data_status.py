"""Tests for /data/status endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_data_status_endpoint_returns_provider_and_scheduler_state() -> None:
    response = client.get("/data/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["fixture_count"] == 72
    assert set(payload["match_status_counts"]) == {
        "scheduled",
        "in_play",
        "finished",
    }
    assert len(payload["providers"]) == 2
    assert payload["scheduler_active_interval_minutes"] == 5
    assert payload["scheduler_idle_interval_minutes"] == 30
    assert "FOOTBALL_DATA_API_TOKEN" not in response.text

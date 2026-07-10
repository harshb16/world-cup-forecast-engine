"""Read-only replay endpoint contract tests."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    TimeMachineManifestResponse,
    TimeMachineMilestoneResponse,
)

client = TestClient(app)


def _manifest() -> TimeMachineManifestResponse:
    return TimeMachineManifestResponse(
        data_version="data-v1",
        model_version="elo",
        simulation_count=10,
        milestones=[
            TimeMachineMilestoneResponse(
                id="before_group_md1",
                label="Before Matchday 1",
                order=0,
                phase="pre_tournament",
                cutoff="group_md0",
                known_result_count=0,
                available=True,
            )
        ],
    )


def test_manifest_endpoint_returns_catalog_without_simulation() -> None:
    with patch("app.api.routes.load_time_machine_manifest", return_value=_manifest()), patch(
        "app.simulation.monte_carlo.run_simulations"
    ) as monte_carlo:
        response = client.get("/time-machine/milestones")

    assert response.status_code == 200
    assert response.json()["milestones"][0]["id"] == "before_group_md1"
    monte_carlo.assert_not_called()


def test_manifest_endpoint_returns_503_when_artifacts_missing() -> None:
    with patch(
        "app.api.routes.load_time_machine_manifest",
        side_effect=FileNotFoundError("missing"),
    ):
        response = client.get("/time-machine/milestones")
    assert response.status_code == 503


def test_snapshot_endpoint_returns_404_for_unavailable_milestone() -> None:
    with patch("app.api.routes.load_time_machine_snapshot", side_effect=KeyError("after_final")):
        response = client.get("/time-machine/milestones/after_final")
    assert response.status_code == 404


def test_archive_probability_history_never_falls_back_to_monte_carlo() -> None:
    with patch(
        "app.api.routes.load_time_machine_probability_history",
        side_effect=FileNotFoundError("missing"),
    ), patch("app.api.routes.is_archive_mode_active", return_value=True), patch(
        "app.api.routes.build_probability_timeline"
    ) as fallback:
        response = client.get("/analytics/probability-history")

    assert response.status_code == 503
    fallback.assert_not_called()

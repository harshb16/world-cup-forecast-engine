"""Tests for analytics API endpoints."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upset_radar_returns_ranked_fixtures() -> None:
    response = client.get("/analytics/upsets?model_type=oracle_v2&limit=8")

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_type"] == "oracle_v2"
    assert len(payload["fixtures"]) <= 8
    assert payload["fixtures"] == sorted(
        payload["fixtures"],
        key=lambda item: item["upset_score"],
        reverse=True,
    )
    first = payload["fixtures"][0]
    assert "risk_label" in first
    assert "reasons" in first
    assert first["favorite_advance_probability"] >= first["underdog_advance_probability"]


def test_group_chaos_returns_all_groups() -> None:
    response = client.get(
        "/analytics/group-chaos?model_type=oracle_v2&n_simulations=40&seed=7"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_type"] == "oracle_v2"
    assert len(payload["groups"]) == 12
    assert all("chaos_score" in group for group in payload["groups"])
    assert payload["groups"] == sorted(
        payload["groups"],
        key=lambda item: item["chaos_score"],
        reverse=True,
    )


def test_model_comparison_response_shape() -> None:
    response = client.get(
        "/analytics/model-comparison?n_simulations=20&seed=11&baseline_model=oracle_v2"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["baseline_model"] == "oracle_v2"
    assert len(payload["top_four_team_ids"]) == 4
    assert set(payload["champion_probabilities"]) == {
        "elo",
        "poisson",
        "calibrated_elo",
        "oracle_v2",
        "dixon_coles",
        "oracle_v3",
    }
    assert len(payload["model_deltas"]) == 5
    for delta in payload["model_deltas"]:
        assert delta["baseline_model"] == "oracle_v2"
        assert len(delta["champion_probability_deltas"]) == 48


def test_model_comparison_defaults_to_calibrated_elo_baseline() -> None:
    response = client.get("/analytics/model-comparison?n_simulations=20&seed=11")

    assert response.status_code == 200
    assert response.json()["baseline_model"] == "calibrated_elo"


def test_data_quality_covers_all_teams() -> None:
    response = client.get("/data-quality")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["teams"]) == 48
    assert payload["source_coverage"]["teams"] == 48
    assert payload["source_coverage"]["groups"] == 12
    assert payload["source_coverage"]["squad_features"] >= 40

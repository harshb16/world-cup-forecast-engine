"""Tests for scenario comparison API endpoint."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _payload(overrides: list[dict] | None = None, n_simulations: int = 8) -> dict:
    return {
        "n_simulations": n_simulations,
        "model_type": "elo",
        "seed": 7,
        "result_overrides": overrides or [],
    }


def test_deltas_are_computed_for_all_teams() -> None:
    response = client.post(
        "/scenario/compare",
        json=_payload([{"match_id": "A1", "team_a_goals": 3, "team_b_goals": 0}]),
    )

    assert response.status_code == 200
    assert len(response.json()["deltas"]) == 48


def test_biggest_risers_sorted_descending() -> None:
    response = client.post(
        "/scenario/compare",
        json=_payload([{"match_id": "A1", "team_a_goals": 3, "team_b_goals": 0}]),
    )

    riser_deltas = [
        item["champion_probability_delta"]
        for item in response.json()["biggest_risers"]
    ]

    assert riser_deltas == sorted(riser_deltas, reverse=True)


def test_biggest_fallers_sorted_ascending() -> None:
    response = client.post(
        "/scenario/compare",
        json=_payload([{"match_id": "A1", "team_a_goals": 3, "team_b_goals": 0}]),
    )

    faller_deltas = [
        item["champion_probability_delta"]
        for item in response.json()["biggest_fallers"]
    ]

    assert faller_deltas == sorted(faller_deltas)


def test_no_overrides_gives_zero_deltas_with_same_seed_and_settings() -> None:
    response = client.post("/scenario/compare", json=_payload())

    assert response.status_code == 200
    for delta in response.json()["deltas"]:
        assert abs(delta["champion_probability_delta"]) < 1e-12
        assert abs(delta["group_qualification_probability_delta"]) < 1e-12


def test_changed_scenario_can_produce_non_zero_deltas() -> None:
    response = client.post(
        "/scenario/compare",
        json=_payload(
            [{"match_id": "A1", "team_a_goals": 6, "team_b_goals": 0}],
            n_simulations=20,
        ),
    )

    deltas = response.json()["deltas"]

    assert any(abs(delta["champion_probability_delta"]) > 0 for delta in deltas)

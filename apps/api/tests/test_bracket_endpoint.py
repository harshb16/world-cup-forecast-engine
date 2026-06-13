"""Tests for interactive bracket trace endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import BracketSimulateRequest
from app.services.bracket_service import run_bracket_simulation


client = TestClient(app)


def test_bracket_simulate_returns_full_knockout_trace() -> None:
    response = client.post(
        "/bracket/simulate",
        json={"model_type": "poisson", "seed": 42},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["n_simulations"] == 1
    assert data["metadata"]["model_type"] == "poisson"
    assert data["simulation_mode"] == "favorite"
    assert len(data["group_tables"]) == 12
    assert len(data["rounds"]["Round of 32"]) == 16
    assert len(data["rounds"]["Round of 16"]) == 8
    assert len(data["rounds"]["Quarter-finals"]) == 4
    assert len(data["rounds"]["Semi-finals"]) == 2
    assert len(data["rounds"]["Final"]) == 1
    assert data["champion_team_id"]
    assert data["champion_team_name"]


def test_bracket_simulate_is_deterministic_with_seed() -> None:
    request = BracketSimulateRequest(model_type="elo", seed=7)

    first = run_bracket_simulation(request, "processed")
    second = run_bracket_simulation(request, "processed")

    assert first == second


def test_favorite_bracket_does_not_pick_lower_advance_probability() -> None:
    result = run_bracket_simulation(
        BracketSimulateRequest(model_type="poisson", simulation_mode="favorite", seed=42),
        "processed",
    )

    for matches in result.rounds.values():
        for match in matches:
            winner_advance_probability = (
                match.probabilities.team_a_advance
                if match.winner_team_id == match.team_a.team_id
                else match.probabilities.team_b_advance
            )
            loser_advance_probability = (
                match.probabilities.team_b_advance
                if match.winner_team_id == match.team_a.team_id
                else match.probabilities.team_a_advance
            )

            assert winner_advance_probability >= loser_advance_probability


def test_random_bracket_still_uses_seeded_stochastic_trace() -> None:
    request = BracketSimulateRequest(
        model_type="poisson",
        simulation_mode="random",
        seed=42,
    )

    first = run_bracket_simulation(request, "processed")
    second = run_bracket_simulation(request, "processed")

    assert first == second
    assert first.simulation_mode == "random"


def test_bracket_probabilities_sum_to_one() -> None:
    result = run_bracket_simulation(
        BracketSimulateRequest(model_type="poisson", seed=3),
        "processed",
    )

    for matches in result.rounds.values():
        for match in matches:
            assert (
                match.probabilities.team_a_win
                + match.probabilities.draw
                + match.probabilities.team_b_win
            ) == pytest.approx(1.0)
            assert (
                match.probabilities.team_a_advance
                + match.probabilities.team_b_advance
            ) == pytest.approx(1.0)


def test_bracket_unknown_override_match_returns_400() -> None:
    response = client.post(
        "/bracket/simulate",
        json={
            "model_type": "poisson",
            "seed": 42,
            "result_overrides": [
                {
                    "match_id": "NOPE",
                    "team_a_goals": 1,
                    "team_b_goals": 0,
                }
            ],
        },
    )

    assert response.status_code == 400

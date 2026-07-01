"""Tests for interactive bracket trace endpoint."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import BracketSimulateRequest, SimulateRequest
from app.services.data_loader import load_tournament
from app.services.bracket_service import (
    _MostLikelyMatchModel,
    _project_favorite_group_stage,
    run_bracket_simulation,
)
from app.services.simulation_service import create_match_model, run_simulation


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


def test_favorite_bracket_projection_ignores_seed() -> None:
    first = run_bracket_simulation(
        BracketSimulateRequest(
            model_type="calibrated_elo",
            simulation_mode="favorite",
            seed=1,
        ),
        "processed",
    )
    second = run_bracket_simulation(
        BracketSimulateRequest(
            model_type="calibrated_elo",
            simulation_mode="favorite",
            seed=999,
        ),
        "processed",
    )

    assert first.rounds == second.rounds
    assert first.champion_team_id == second.champion_team_id


def test_favorite_bracket_uses_the_selected_models_ratings() -> None:
    config = load_tournament("processed")
    base_model = create_match_model("calibrated_elo", "processed")
    favorite_model = _MostLikelyMatchModel(base_model)

    for team in config.teams:
        assert favorite_model.rating_for(team) == pytest.approx(
            base_model.rating_for(team)
        )


def test_favorite_finalists_are_dashboard_title_contenders() -> None:
    forecast = run_simulation(
        SimulateRequest(
            n_simulations=1000,
            model_type="calibrated_elo",
            seed=42,
        ),
        "processed",
    )
    bracket = run_bracket_simulation(
        BracketSimulateRequest(
            model_type="calibrated_elo",
            simulation_mode="favorite",
            seed=42,
        ),
        "processed",
    )
    top_contenders = {
        team.team_id
        for team in sorted(
            forecast.teams,
            key=lambda team: team.champion,
            reverse=True,
        )[:8]
    }
    final = bracket.rounds["Final"][0]

    assert {final.team_a.team_id, final.team_b.team_id}.issubset(top_contenders)


def test_favorite_bracket_projects_groups_from_favorite_path() -> None:
    config = load_tournament("processed")
    match_model = _MostLikelyMatchModel(create_match_model("calibrated_elo", "processed"))
    expected = _project_favorite_group_stage(config, match_model)

    result = run_bracket_simulation(
        BracketSimulateRequest(
            model_type="calibrated_elo",
            simulation_mode="favorite",
            seed=42,
        ),
        "processed",
    )

    projected_group_winners = {
        table.group_id: table.rows[0]["team_id"]
        for table in result.group_tables
    }
    expected_group_winners = {
        group_id: rows[0].team_id
        for group_id, rows in expected.group_tables.items()
    }
    assert projected_group_winners == expected_group_winners


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


def test_oracle_v3_favorite_path_uses_expected_group_projection() -> None:
    result = run_bracket_simulation(
        BracketSimulateRequest(model_type="oracle_v3", simulation_mode="favorite", seed=42),
        "processed",
    )

    round_of_16_team_ids = {
        match.team_a.team_id
        for match in result.rounds["Round of 16"]
    } | {
        match.team_b.team_id
        for match in result.rounds["Round of 16"]
    }
    semifinal_pair = result.rounds["Semi-finals"][0]

    assert len(round_of_16_team_ids) == 16
    assert {semifinal_pair.team_a.team_id, semifinal_pair.team_b.team_id} == {
        "FRANCE",
        "SPAIN",
    }
    assert result.rounds["Final"][0].team_a_expected_goals is not None
    assert result.rounds["Final"][0].confidence_label


def test_bracket_result_is_real_false_without_knockout_fixtures() -> None:
    result = run_bracket_simulation(
        BracketSimulateRequest(model_type="poisson", seed=42),
        "processed",
    )

    for matches in result.rounds.values():
        for match in matches:
            assert match.result_is_real is False


def test_bracket_result_is_real_true_for_played_knockout_fixture() -> None:
    from app.models.domain import MatchResult
    from app.services.bracket_materialization_service import materialize_round_of_32_if_ready

    config = load_tournament("sample")
    completed_groups = [
        match.model_copy(
            update={
                "result": MatchResult(team_a_goals=2, team_b_goals=1, played=True),
                "winner_team_id": match.team_a_id,
            }
        )
        for match in config.matches
        if match.stage == "group"
    ]
    config = config.model_copy(update={"matches": completed_groups})
    r32 = materialize_round_of_32_if_ready(config)
    first = r32[0].model_copy(
        update={
            "result": MatchResult(team_a_goals=1, team_b_goals=0, played=True),
            "winner_team_id": r32[0].team_a_id,
        }
    )
    config = config.model_copy(
        update={"matches": [*completed_groups, first, *r32[1:]]}
    )

    from app.services.data_loader import load_sample_tournament
    from unittest.mock import patch

    with patch("app.services.bracket_service.load_tournament", return_value=config):
        result = run_bracket_simulation(
            BracketSimulateRequest(
                model_type="poisson",
                simulation_mode="random",
                seed=42,
            ),
            "sample",
        )

    real_matches = [
        match
        for stage_matches in result.rounds.values()
        for match in stage_matches
        if match.result_is_real
    ]
    assert len(real_matches) == 1
    assert real_matches[0].winner_team_id == first.team_a_id


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

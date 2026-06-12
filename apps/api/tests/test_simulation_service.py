"""Tests for simulation service orchestration."""

import pytest

from app.models.domain import MatchResult
from app.models.schemas import MatchResultOverride, ScenarioSimulateRequest, SimulateRequest
from app.services.data_loader import load_sample_tournament
from app.services.simulation_service import (
    apply_result_overrides,
    create_match_model,
    run_sample_simulation,
)
from app.simulation.match_models import EloWinDrawLossModel, PoissonScoreModel


def test_create_match_model_accepts_valid_models() -> None:
    assert isinstance(create_match_model("elo"), EloWinDrawLossModel)
    assert isinstance(create_match_model("poisson"), PoissonScoreModel)


def test_create_match_model_rejects_invalid_model_type() -> None:
    with pytest.raises(ValueError, match="unsupported model_type"):
        create_match_model("not-real")


def test_simulation_service_returns_all_48_teams() -> None:
    response = run_sample_simulation(
        SimulateRequest(n_simulations=3, model_type="elo", seed=1)
    )

    assert len(response.teams) == 48


def test_overrides_mark_matches_as_played() -> None:
    config = load_sample_tournament()

    updated = apply_result_overrides(
        config,
        [MatchResultOverride(match_id=config.matches[0].id, team_a_goals=2, team_b_goals=1)],
    )

    assert updated.matches[0].result == MatchResult(team_a_goals=2, team_b_goals=1)


def test_invalid_match_id_raises_clear_error() -> None:
    config = load_sample_tournament()

    with pytest.raises(ValueError, match="unknown match_id"):
        apply_result_overrides(
            config,
            [MatchResultOverride(match_id="missing", team_a_goals=1, team_b_goals=0)],
        )


def test_scenario_request_accepts_overrides() -> None:
    request = ScenarioSimulateRequest(
        n_simulations=3,
        model_type="elo",
        seed=1,
        result_overrides=[
            MatchResultOverride(match_id="A1", team_a_goals=2, team_b_goals=0)
        ],
    )

    assert len(request.result_overrides) == 1

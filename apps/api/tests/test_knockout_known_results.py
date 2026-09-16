"""Tests for knockout simulation with known real-world results."""

import numpy as np

from app.models.domain import Match, MatchResult
from app.services.data_loader import load_sample_tournament
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import (
    WorldCup2026BracketBuilder,
    build_known_knockout_results,
    simulate_knockout,
)
from app.simulation.match_models import EloWinDrawLossModel
from app.simulation.simulation_trace import run_simulation_trace


class AlwaysWinTeamAModel(EloWinDrawLossModel):
    def simulate_result(self, team_a, team_b, rng, stage=None):  # type: ignore[no-untyped-def]
        return MatchResult(team_a_goals=3, team_b_goals=0)


def _sample_qualifiers_and_teams():
    config = load_sample_tournament()
    group_stage = simulate_group_stage(
        config,
        EloWinDrawLossModel(),
        np.random.default_rng(1),
    )
    teams_by_id = {team.id: team for team in config.teams}
    return group_stage.qualified_team_ids, teams_by_id


def test_known_r32_result_is_used_instead_of_simulation() -> None:
    qualified_team_ids, teams_by_id = _sample_qualifiers_and_teams()
    pairs = WorldCup2026BracketBuilder().build_round_of_32(
        qualified_team_ids,
        teams_by_id,
    )
    team_a_id, team_b_id = pairs[0]
    known_match = Match(
        id="R32-01",
        stage="Round of 32",
        team_a_id=team_a_id,
        team_b_id=team_b_id,
        result=MatchResult(team_a_goals=2, team_b_goals=1, played=True),
        winner_team_id=team_b_id,
    )
    known = build_known_knockout_results([known_match])

    result = simulate_knockout(
        qualified_team_ids,
        teams_by_id,
        AlwaysWinTeamAModel(),
        np.random.default_rng(99),
        known_results=known,
    )

    first_match = result.rounds["Round of 32"][0]
    assert first_match.result == known_match.result
    assert first_match.winner_team_id == team_b_id


def test_partial_r32_round_mixes_real_and_simulated_winners() -> None:
    qualified_team_ids, teams_by_id = _sample_qualifiers_and_teams()
    pairs = WorldCup2026BracketBuilder().build_round_of_32(
        qualified_team_ids,
        teams_by_id,
    )
    team_a_id, team_b_id = pairs[0]
    known = build_known_knockout_results(
        [
            Match(
                id="R32-01",
                stage="Round of 32",
                team_a_id=team_a_id,
                team_b_id=team_b_id,
                result=MatchResult(team_a_goals=0, team_b_goals=1, played=True),
                winner_team_id=team_b_id,
            )
        ]
    )

    result = simulate_knockout(
        qualified_team_ids,
        teams_by_id,
        AlwaysWinTeamAModel(),
        np.random.default_rng(7),
        known_results=known,
    )

    assert result.rounds["Round of 32"][0].winner_team_id == team_b_id
    assert all(
        match.winner_team_id is not None
        for match in result.rounds["Round of 32"]
    )


def test_simulation_trace_accepts_config_with_known_knockout_fixtures() -> None:
    config = load_sample_tournament()
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
    from app.services.bracket_materialization_service import materialize_round_of_32_if_ready

    config = config.model_copy(update={"matches": completed_groups})
    r32 = materialize_round_of_32_if_ready(config)
    first = r32[0]
    real_first = first.model_copy(
        update={
            "result": MatchResult(team_a_goals=0, team_b_goals=2, played=True),
            "winner_team_id": first.team_b_id,
        }
    )
    config = config.model_copy(
        update={"matches": [*completed_groups, real_first, *r32[1:]]}
    )
    team_index = {team.id: index for index, team in enumerate(config.teams)}
    trace = run_simulation_trace(
        config,
        EloWinDrawLossModel(),
        seed=42,
        team_index=team_index,
    )
    assert trace[0] >= 0

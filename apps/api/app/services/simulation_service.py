"""Simulation service orchestration."""

from app.models.domain import MatchResult, SimulationSummary, Team, TournamentConfig
from app.models.schemas import (
    MatchResultOverride,
    ScenarioSimulateRequest,
    SimulateRequest,
    SimulationMetadataResponse,
    SimulationSummaryResponse,
    TeamStageProbabilityResponse,
)
from app.services.data_loader import load_sample_tournament
from app.simulation.match_models import EloWinDrawLossModel, MatchModel, PoissonScoreModel
from app.simulation.monte_carlo import STAGES, run_simulations


def create_match_model(model_type: str) -> MatchModel:
    """Create a match model from a public model type."""
    if model_type == "elo":
        return EloWinDrawLossModel()
    if model_type == "poisson":
        return PoissonScoreModel()
    raise ValueError(f"unsupported model_type: {model_type}")


def run_sample_simulation(request: SimulateRequest) -> SimulationSummaryResponse:
    """Run a simulation against the local sample tournament."""
    config = load_sample_tournament()
    summary = run_simulations(
        config,
        create_match_model(request.model_type),
        n_simulations=request.n_simulations,
        seed=request.seed,
    )
    metadata = SimulationMetadataResponse(
        n_simulations=request.n_simulations,
        model_type=request.model_type,
        seed=request.seed,
    )

    return _to_response(summary, config.teams, metadata)


def apply_result_overrides(
    config: TournamentConfig,
    overrides: list[MatchResultOverride],
) -> TournamentConfig:
    """Apply manual result overrides to tournament matches."""
    matches_by_id = {match.id: match for match in config.matches}
    unknown_match_ids = [
        override.match_id
        for override in overrides
        if override.match_id not in matches_by_id
    ]
    if unknown_match_ids:
        raise ValueError(f"unknown match_id: {unknown_match_ids[0]}")

    overrides_by_match_id = {override.match_id: override for override in overrides}
    updated_matches = []
    for match in config.matches:
        override = overrides_by_match_id.get(match.id)
        if override is None:
            updated_matches.append(match)
            continue

        updated_matches.append(
            match.model_copy(
                update={
                    "result": MatchResult(
                        team_a_goals=override.team_a_goals,
                        team_b_goals=override.team_b_goals,
                        played=True,
                    )
                }
            )
        )

    return TournamentConfig(
        teams=config.teams,
        groups=config.groups,
        matches=updated_matches,
    )


def run_sample_scenario_simulation(
    request: ScenarioSimulateRequest,
) -> SimulationSummaryResponse:
    """Run a sample tournament simulation with manual result overrides."""
    config = apply_result_overrides(
        load_sample_tournament(),
        request.result_overrides,
    )
    summary = run_simulations(
        config,
        create_match_model(request.model_type),
        n_simulations=request.n_simulations,
        seed=request.seed,
    )
    metadata = SimulationMetadataResponse(
        n_simulations=request.n_simulations,
        model_type=request.model_type,
        seed=request.seed,
        overrides_applied=request.result_overrides,
    )

    return _to_response(summary, config.teams, metadata)


def _to_response(
    summary: SimulationSummary,
    teams: list[Team],
    metadata: SimulationMetadataResponse,
) -> SimulationSummaryResponse:
    teams_by_id = {team.id: team for team in teams}
    team_responses = [
        TeamStageProbabilityResponse(
            team_id=team_id,
            team_name=teams_by_id[team_id].name,
            group_id=teams_by_id[team_id].group_id,
            group_stage_exit=stage_probabilities["group_stage_exit"],
            round_of_32=stage_probabilities["round_of_32"],
            round_of_16=stage_probabilities["round_of_16"],
            quarter_final=stage_probabilities["quarter_final"],
            semi_final=stage_probabilities["semi_final"],
            final=stage_probabilities["final"],
            champion=stage_probabilities["champion"],
            group_qualification_probability=summary.group_qualification_probability[team_id],
            top_two_probability=summary.top_two_probability[team_id],
            third_place_finish_probability=summary.third_place_finish_probability[team_id],
            third_place_qualification_probability=summary.third_place_qualification_probability[team_id],
            average_points=summary.average_points_by_team[team_id],
        )
        for team_id, stage_probabilities in summary.stage_probabilities.items()
    ]

    return SimulationSummaryResponse(
        metadata=metadata,
        teams=team_responses,
        champion_probabilities={
            team_id: summary.stage_probabilities[team_id]["champion"]
            for team_id in summary.stage_probabilities
        },
        group_qualification_probabilities=summary.group_qualification_probability,
        top_two_probabilities=summary.top_two_probability,
        third_place_finish_probabilities=summary.third_place_finish_probability,
        third_place_qualification_probabilities=summary.third_place_qualification_probability,
        average_points_by_team=summary.average_points_by_team,
    )

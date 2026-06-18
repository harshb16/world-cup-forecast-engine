"""Simulation service orchestration."""

from app.models.domain import MatchResult, SimulationSummary, Team, TournamentConfig
from app.models.schemas import (
    MatchResultOverride,
    ScenarioCompareResponse,
    ScenarioSimulateRequest,
    SimulateRequest,
    SimulationMetadataResponse,
    SimulationSummaryResponse,
    TeamProbabilityDeltaResponse,
    TeamStageProbabilityResponse,
)
from app.services.data_loader import (
    load_metadata,
    load_model_parameters,
    load_squad_features,
    load_tournament,
)
from app.simulation.match_models import (
    DixonColesModel,
    EloWinDrawLossModel,
    MatchModel,
    OracleV2Model,
    PoissonScoreModel,
)
from app.simulation.monte_carlo import STAGES, run_simulations


def create_match_model(model_type: str, data_mode: str = "processed") -> MatchModel:
    """Create a match model from a public model type."""
    if model_type == "elo":
        return EloWinDrawLossModel()
    if model_type == "calibrated_elo":
        parameters = load_model_parameters(data_mode)
        return EloWinDrawLossModel(
            rating_overrides={
                item["team_id"]: item["rating"]
                for item in parameters.get("team_ratings", [])
                if not item.get("fallback_used", False)
            }
        )
    if model_type == "poisson":
        return PoissonScoreModel()
    if model_type == "dixon_coles":
        return DixonColesModel()
    if model_type == "oracle_v2":
        parameters = load_model_parameters(data_mode)
        return OracleV2Model(
            rating_overrides={
                item["team_id"]: item["rating"]
                for item in parameters.get("team_ratings", [])
                if not item.get("fallback_used", False)
            },
            squad_features=load_squad_features(data_mode),
        )
    raise ValueError(f"unsupported model_type: {model_type}")


def run_simulation(request: SimulateRequest, data_mode: str) -> SimulationSummaryResponse:
    """Run a simulation against the configured tournament data."""
    config = load_tournament(data_mode)
    summary = run_simulations(
        config,
        create_match_model(request.model_type, data_mode),
        n_simulations=request.n_simulations,
        seed=request.seed,
    )
    metadata = _simulation_metadata(request, data_mode)

    return _to_response(summary, config.teams, metadata)


def run_sample_simulation(request: SimulateRequest) -> SimulationSummaryResponse:
    """Run a simulation against the local sample tournament."""
    return run_simulation(request, "sample")


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


def run_scenario_simulation(
    request: ScenarioSimulateRequest,
    data_mode: str,
) -> SimulationSummaryResponse:
    """Run a tournament simulation with manual result overrides."""
    config = apply_result_overrides(
        load_tournament(data_mode),
        request.result_overrides,
    )
    summary = run_simulations(
        config,
        create_match_model(request.model_type, data_mode),
        n_simulations=request.n_simulations,
        seed=request.seed,
    )
    metadata = _simulation_metadata(request, data_mode)

    return _to_response(summary, config.teams, metadata)


def run_sample_scenario_simulation(
    request: ScenarioSimulateRequest,
) -> SimulationSummaryResponse:
    """Run a sample tournament simulation with manual result overrides."""
    return run_scenario_simulation(request, "sample")


def run_scenario_compare(
    request: ScenarioSimulateRequest,
    data_mode: str,
) -> ScenarioCompareResponse:
    """Compare baseline simulation probabilities against a scenario."""
    baseline_request = SimulateRequest(
        n_simulations=request.n_simulations,
        model_type=request.model_type,
        seed=request.seed,
    )
    baseline = run_simulation(baseline_request, data_mode)
    scenario = run_scenario_simulation(request, data_mode)
    deltas = _calculate_deltas(baseline, scenario)
    ranked_by_champion_delta = sorted(
        deltas,
        key=lambda item: item.champion_probability_delta,
        reverse=True,
    )

    return ScenarioCompareResponse(
        baseline=baseline,
        scenario=scenario,
        deltas=deltas,
        biggest_risers=ranked_by_champion_delta[:5],
        biggest_fallers=sorted(deltas, key=lambda item: item.champion_probability_delta)[:5],
    )


def run_sample_scenario_compare(
    request: ScenarioSimulateRequest,
) -> ScenarioCompareResponse:
    """Compare baseline simulation probabilities against a scenario."""
    return run_scenario_compare(request, "sample")


def _simulation_metadata(
    request: SimulateRequest,
    data_mode: str,
) -> SimulationMetadataResponse:
    source_metadata = load_metadata(data_mode)
    overrides = (
        request.result_overrides
        if isinstance(request, ScenarioSimulateRequest)
        else []
    )
    return SimulationMetadataResponse(
        n_simulations=request.n_simulations,
        model_type=request.model_type,
        seed=request.seed,
        overrides_applied=overrides,
        **source_metadata,
    )


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


def _calculate_deltas(
    baseline: SimulationSummaryResponse,
    scenario: SimulationSummaryResponse,
) -> list[TeamProbabilityDeltaResponse]:
    baseline_by_team = {team.team_id: team for team in baseline.teams}
    scenario_by_team = {team.team_id: team for team in scenario.teams}

    return [
        TeamProbabilityDeltaResponse(
            team_id=team_id,
            team_name=scenario_team.team_name,
            group_id=scenario_team.group_id,
            champion_probability_delta=scenario_team.champion - baseline_team.champion,
            final_probability_delta=scenario_team.final - baseline_team.final,
            semi_final_probability_delta=scenario_team.semi_final - baseline_team.semi_final,
            quarter_final_probability_delta=scenario_team.quarter_final - baseline_team.quarter_final,
            round_of_16_probability_delta=scenario_team.round_of_16 - baseline_team.round_of_16,
            round_of_32_probability_delta=scenario_team.round_of_32 - baseline_team.round_of_32,
            group_qualification_probability_delta=(
                scenario_team.group_qualification_probability
                - baseline_team.group_qualification_probability
            ),
        )
        for team_id, scenario_team in scenario_by_team.items()
        for baseline_team in [baseline_by_team[team_id]]
    ]

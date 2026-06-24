"""Team path explorer service."""

from collections import Counter

import numpy as np

from app.models.schemas import (
    BracketTeamResponse,
    SimulationMetadataResponse,
    TeamPathMostLikelyOpponentResponse,
    TeamPathOpponentResponse,
    TeamPathRequest,
    TeamPathResponse,
    TeamPathStageResponse,
)
from app.services.data_loader import load_metadata, load_tournament
from app.services.simulation_service import create_match_model
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import ROUND_NAMES, simulate_knockout


def calculate_team_path(
    request: TeamPathRequest,
    data_mode: str,
) -> TeamPathResponse:
    """Calculate likely knockout opponents for one team."""
    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
    if request.team_id not in teams_by_id:
        raise ValueError(f"unknown team_id: {request.team_id}")

    match_model = create_match_model(request.model_type, data_mode)
    rng = np.random.default_rng(request.seed)
    reached_counts = {stage: 0 for stage in ROUND_NAMES}
    opponent_counts = {stage: Counter() for stage in ROUND_NAMES}

    for _ in range(request.n_simulations):
        group_stage = simulate_group_stage(config, match_model, rng)
        if request.team_id not in group_stage.qualified_team_ids:
            continue

        knockout = simulate_knockout(
            group_stage.qualified_team_ids,
            teams_by_id,
            match_model,
            rng,
        )
        for stage in ROUND_NAMES:
            match = next(
                (
                    candidate
                    for candidate in knockout.rounds[stage]
                    if request.team_id
                    in {candidate.team_a_id, candidate.team_b_id}
                ),
                None,
            )
            if match is None:
                continue

            opponent_id = (
                match.team_b_id
                if match.team_a_id == request.team_id
                else match.team_a_id
            )
            reached_counts[stage] += 1
            opponent_counts[stage][opponent_id] += 1

            if match.winner_team_id != request.team_id:
                break

    team = teams_by_id[request.team_id]
    metadata = SimulationMetadataResponse(
        n_simulations=request.n_simulations,
        model_type=request.model_type,
        seed=request.seed,
        **load_metadata(data_mode),
    )

    return TeamPathResponse(
        metadata=metadata,
        team=BracketTeamResponse(
            team_id=team.id,
            team_name=team.name,
            group_id=team.group_id,
            rating=team.rating,
        ),
        stages=[
            _build_stage_response(
                stage,
                reached_counts[stage],
                opponent_counts[stage],
                teams_by_id,
                request.n_simulations,
            )
            for stage in ROUND_NAMES
        ],
    )


def _build_stage_response(
    stage: str,
    reached_count: int,
    opponent_counter: Counter[str],
    teams_by_id: dict[str, object],
    n_simulations: int,
) -> TeamPathStageResponse:
    opponents = [
        TeamPathOpponentResponse(
            team_id=opponent_id,
            team_name=teams_by_id[opponent_id].name,
            count=count,
            probability=count / n_simulations,
        )
        for opponent_id, count in opponent_counter.most_common(5)
    ]
    most_likely = None
    if opponents:
        top = opponents[0]
        most_likely = TeamPathMostLikelyOpponentResponse(
            team_id=top.team_id,
            team_name=top.team_name,
            probability=top.probability,
        )
    return TeamPathStageResponse(
        stage=stage,
        reached_count=reached_count,
        reached_probability=reached_count / n_simulations,
        opponents=opponents,
        most_likely_opponent=most_likely,
    )

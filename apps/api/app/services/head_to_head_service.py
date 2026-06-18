"""Head-to-head meeting probability between two teams."""

import numpy as np

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.schemas import HeadToHeadResponse
from app.services.data_loader import load_tournament
from app.services.simulation_service import create_match_model
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import ROUND_NAMES, simulate_knockout


def calculate_head_to_head(
    team_a_id: str,
    team_b_id: str,
    data_mode: str,
    model_type: str = DEFAULT_MODEL_TYPE,
    n_simulations: int = 500,
    seed: int = 42,
) -> HeadToHeadResponse:
    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
    if team_a_id not in teams_by_id or team_b_id not in teams_by_id:
        raise ValueError("unknown team_id")

    match_model = create_match_model(model_type, data_mode)
    rng = np.random.default_rng(seed)
    meet_before_final = 0
    meet_semi = 0
    meet_final = 0

    for _ in range(n_simulations):
        group_stage = simulate_group_stage(config, match_model, rng)
        qualified = set(group_stage.qualified_team_ids)
        if team_a_id not in qualified or team_b_id not in qualified:
            continue
        knockout = simulate_knockout(
            group_stage.qualified_team_ids,
            teams_by_id,
            match_model,
            rng,
        )
        for stage in ROUND_NAMES:
            for match in knockout.rounds[stage]:
                pair = {match.team_a_id, match.team_b_id}
                if team_a_id in pair and team_b_id in pair:
                    if stage == "Final":
                        meet_final += 1
                        meet_before_final += 1
                    elif stage == "Semi-finals":
                        meet_semi += 1
                        meet_before_final += 1
                    break

    return HeadToHeadResponse(
        team_a_id=team_a_id,
        team_a_name=teams_by_id[team_a_id].name,
        team_b_id=team_b_id,
        team_b_name=teams_by_id[team_b_id].name,
        meet_before_final_probability=meet_before_final / n_simulations,
        meet_in_semi_final_probability=meet_semi / n_simulations,
        meet_in_final_probability=meet_final / n_simulations,
        n_simulations=n_simulations,
    )

"""Head-to-head meeting probability between two teams."""

from collections import Counter

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
    if n_simulations < 1:
        raise ValueError("n_simulations must be at least 1")
    if team_a_id == team_b_id:
        raise ValueError("team ids must be different")

    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
    if team_a_id not in teams_by_id or team_b_id not in teams_by_id:
        raise ValueError("unknown team_id")

    match_model = create_match_model(model_type, data_mode)
    rng = np.random.default_rng(seed)
    meeting_counts: Counter[str] = Counter()

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
                    meeting_counts[stage] += 1
                    break

    total_meetings = sum(meeting_counts.values())
    meetings_before_final = sum(
        count for stage, count in meeting_counts.items() if stage != "Final"
    )

    return HeadToHeadResponse(
        team_a_id=team_a_id,
        team_a_name=teams_by_id[team_a_id].name,
        team_b_id=team_b_id,
        team_b_name=teams_by_id[team_b_id].name,
        probability=total_meetings / n_simulations,
        stages_they_could_meet=[
            stage for stage in ROUND_NAMES if meeting_counts[stage] > 0
        ],
        meet_before_final_probability=meetings_before_final / n_simulations,
        meet_in_semi_final_probability=meeting_counts["Semi-finals"] / n_simulations,
        meet_in_final_probability=meeting_counts["Final"] / n_simulations,
        n_simulations=n_simulations,
    )

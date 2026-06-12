"""Monte Carlo aggregation module."""

import numpy as np

from app.models.domain import SimulationSummary, TournamentConfig
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import simulate_knockout
from app.simulation.match_models import MatchModel

STAGES = [
    "group_stage_exit",
    "round_of_32",
    "round_of_16",
    "quarter_final",
    "semi_final",
    "final",
    "champion",
]

ELIMINATION_STAGE_TO_SUMMARY_STAGE = {
    "Round of 32": "round_of_32",
    "Round of 16": "round_of_16",
    "Quarter-finals": "quarter_final",
    "Semi-finals": "semi_final",
    "Final": "final",
    "Champion": "champion",
}


def run_simulations(
    config: TournamentConfig,
    match_model: MatchModel,
    n_simulations: int,
    seed: int | None = None,
) -> SimulationSummary:
    """Run full-tournament Monte Carlo simulations and aggregate probabilities."""
    if n_simulations <= 0:
        raise ValueError("n_simulations must be positive")

    rng = np.random.default_rng(seed)
    team_ids = [team.id for team in config.teams]
    teams_by_id = {team.id: team for team in config.teams}
    stage_counts = {
        team_id: {stage: 0 for stage in STAGES}
        for team_id in team_ids
    }
    points_total = {team_id: 0 for team_id in team_ids}
    group_qualification_counts = {team_id: 0 for team_id in team_ids}
    top_two_counts = {team_id: 0 for team_id in team_ids}
    third_place_finish_counts = {team_id: 0 for team_id in team_ids}
    third_place_qualification_counts = {team_id: 0 for team_id in team_ids}

    for _ in range(n_simulations):
        group_stage = simulate_group_stage(config, match_model, rng)
        qualified_team_ids = set(group_stage.qualified_team_ids)
        top_two_team_ids = set(group_stage.top_two_qualifiers)
        third_place_team_ids = {row.team_id for row in group_stage.third_place_rankings}
        third_place_qualifier_ids = set(group_stage.third_place_qualifiers)

        for table in group_stage.group_tables.values():
            for row in table:
                points_total[row.team_id] += row.points

        for team_id in team_ids:
            if team_id in qualified_team_ids:
                group_qualification_counts[team_id] += 1
            else:
                stage_counts[team_id]["group_stage_exit"] += 1
            if team_id in top_two_team_ids:
                top_two_counts[team_id] += 1
            if team_id in third_place_team_ids:
                third_place_finish_counts[team_id] += 1
            if team_id in third_place_qualifier_ids:
                third_place_qualification_counts[team_id] += 1

        knockout = simulate_knockout(
            group_stage.qualified_team_ids,
            teams_by_id,
            match_model,
            rng,
        )
        for team_id, elimination_stage in knockout.eliminated_stage_by_team.items():
            summary_stage = ELIMINATION_STAGE_TO_SUMMARY_STAGE[elimination_stage]
            stage_counts[team_id][summary_stage] += 1

    return SimulationSummary(
        stage_probabilities={
            team_id: {
                stage: stage_counts[team_id][stage] / n_simulations
                for stage in STAGES
            }
            for team_id in team_ids
        },
        average_points_by_team={
            team_id: points_total[team_id] / n_simulations
            for team_id in team_ids
        },
        group_qualification_probability={
            team_id: group_qualification_counts[team_id] / n_simulations
            for team_id in team_ids
        },
        top_two_probability={
            team_id: top_two_counts[team_id] / n_simulations
            for team_id in team_ids
        },
        third_place_finish_probability={
            team_id: third_place_finish_counts[team_id] / n_simulations
            for team_id in team_ids
        },
        third_place_qualification_probability={
            team_id: third_place_qualification_counts[team_id] / n_simulations
            for team_id in team_ids
        },
    )

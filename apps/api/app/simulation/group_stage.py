"""Group-stage simulation module."""

import numpy as np

from app.models.domain import GroupStageResult, Match, TournamentConfig
from app.simulation.group_table import calculate_group_table
from app.simulation.match_models import MatchModel
from app.simulation.third_place import get_best_third_place_qualifiers, rank_third_place_teams


def simulate_group_stage(
    config: TournamentConfig,
    match_model: MatchModel,
    rng: np.random.Generator,
) -> GroupStageResult:
    """Simulate all unplayed group-stage matches and calculate qualifiers."""
    teams_by_id = {team.id: team for team in config.teams}
    group_matches: list[Match] = []

    for match in config.matches:
        if match.stage != "group":
            continue
        if match.result is not None and match.result.played:
            group_matches.append(match)
            continue

        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        result = match_model.simulate_result(team_a, team_b, rng)
        group_matches.append(match.model_copy(update={"result": result}))

    group_tables = {
        group.id: calculate_group_table(group, teams_by_id, group_matches)
        for group in sorted(config.groups, key=lambda item: item.id)
    }

    top_two_qualifiers = [
        row.team_id
        for group_id in sorted(group_tables)
        for row in group_tables[group_id][:2]
    ]
    third_place_rankings = rank_third_place_teams(group_tables)
    third_place_qualifier_rows = get_best_third_place_qualifiers(group_tables, count=8)
    third_place_qualifiers = [row.team_id for row in third_place_qualifier_rows]
    qualified_team_ids = top_two_qualifiers + third_place_qualifiers

    return GroupStageResult(
        simulated_matches=group_matches,
        group_tables=group_tables,
        top_two_qualifiers=top_two_qualifiers,
        third_place_rankings=third_place_rankings,
        third_place_qualifiers=third_place_qualifiers,
        qualified_team_ids=qualified_team_ids,
    )

"""Third-place qualification bubble tracker."""

from collections import Counter

import numpy as np

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.schemas import (
    ModelType,
    ThirdPlaceSlotDistributionResponse,
    ThirdPlaceTeamResponse,
    ThirdPlaceTrackerResponse,
)
from app.services.data_loader import load_tournament
from app.services.simulation_service import create_match_model
from app.simulation.group_stage import simulate_group_stage
from app.simulation.group_table import calculate_group_table
from app.simulation.knockout import WorldCup2026BracketBuilder


def calculate_third_place_tracker(
    data_mode: str,
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    n_simulations: int = 500,
    seed: int = 42,
) -> ThirdPlaceTrackerResponse:
    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
    match_model = create_match_model(model_type, data_mode)
    rng = np.random.default_rng(seed)
    builder = WorldCup2026BracketBuilder()
    group_matches = [m for m in config.matches if m.stage == "group"]
    third_place_ids = {
        team_id
        for team_id in teams_by_id
        if _is_third_place_candidate(team_id, config, group_matches, teams_by_id)
    }
    qualification_counts: Counter[str] = Counter()
    slot_counts: dict[str, Counter[str]] = {}
    points_samples: dict[str, list[float]] = {}
    current_tables = {
        group.id: {
            row.team_id: row.points
            for row in calculate_group_table(group, teams_by_id, group_matches)
        }
        for group in config.groups
    }
    for _ in range(n_simulations):
        group_stage = simulate_group_stage(config, match_model, rng)
        for team_id in third_place_ids:
            qualification_counts[team_id] += int(
                team_id in group_stage.third_place_qualifiers
            )
        for row in group_stage.third_place_rankings:
            if row.team_id in third_place_ids:
                points_samples.setdefault(row.team_id, []).append(float(row.points))
        try:
            pairs = builder.build_round_of_32(
                group_stage.qualified_team_ids,
                teams_by_id,
            )
        except ValueError:
            continue
        for index, (team_a_id, team_b_id) in enumerate(pairs, start=1):
            slot_label = f"R32-{index:02d}"
            for team_id in (team_a_id, team_b_id):
                if team_id in group_stage.third_place_qualifiers:
                    slot_counts.setdefault(team_id, Counter())[slot_label] += 1
    teams = []
    for team_id in sorted(
        third_place_ids,
        key=lambda tid: qualification_counts.get(tid, 0),
        reverse=True,
    ):
        team = teams_by_id[team_id]
        slot_counter = slot_counts.get(team_id, Counter())
        total_slots = sum(slot_counter.values()) or 1
        samples = points_samples.get(team_id, [])
        teams.append(
            ThirdPlaceTeamResponse(
                team_id=team_id,
                team_name=team.name,
                group_id=team.group_id,
                qualification_probability=qualification_counts.get(team_id, 0) / n_simulations,
                current_points=current_tables[team.group_id].get(team_id, 0),
                simulated_average_points=sum(samples) / len(samples) if samples else 0.0,
                slot_distribution=[
                    ThirdPlaceSlotDistributionResponse(
                        slot_label=label,
                        probability=count / total_slots,
                    )
                    for label, count in slot_counter.most_common()
                ],
            )
        )
    return ThirdPlaceTrackerResponse(
        model_type=model_type,
        data_mode=data_mode,
        n_simulations=n_simulations,
        teams=teams,
    )


def _is_third_place_candidate(team_id, config, group_matches, teams_by_id):
    team = teams_by_id[team_id]
    group = next(g for g in config.groups if g.id == team.group_id)
    table = calculate_group_table(group, teams_by_id, group_matches)
    return any(row.team_id == team_id and index == 2 for index, row in enumerate(table))

"""Compact single-tournament simulation traces for bank storage."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.models.domain import TournamentConfig
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import ROUND_NAMES, simulate_knockout
from app.simulation.match_models import MatchModel
from app.simulation.monte_carlo import ELIMINATION_STAGE_TO_SUMMARY_STAGE, STAGES

QUALIFIER_COUNT = 32


@dataclass(frozen=True)
class SimulationBatchTrace:
    """Arrays produced by one simulation batch."""

    champions: np.ndarray
    qualified: np.ndarray
    top_two: np.ndarray
    third_finish: np.ndarray
    third_qualified: np.ndarray
    points: np.ndarray
    max_stage: np.ndarray
    qualifier_order: np.ndarray
    knockout_opponents: np.ndarray


def run_simulation_trace(
    config: TournamentConfig,
    match_model: MatchModel,
    seed: int,
    team_index: dict[str, int],
) -> tuple[
    int,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Return champion index and per-team trace arrays for one simulation."""
    rng = np.random.default_rng(seed)
    teams_by_id = {team.id: team for team in config.teams}
    team_count = len(team_index)
    group_stage = simulate_group_stage(config, match_model, rng)
    knockout = simulate_knockout(
        group_stage.qualified_team_ids,
        teams_by_id,
        match_model,
        rng,
    )

    qualified = np.zeros(team_count, dtype=np.bool_)
    top_two = np.zeros(team_count, dtype=np.bool_)
    third_finish = np.zeros(team_count, dtype=np.bool_)
    third_qualified = np.zeros(team_count, dtype=np.bool_)
    points = np.zeros(team_count, dtype=np.uint8)
    max_stage = np.zeros(team_count, dtype=np.uint8)

    qualified_ids = set(group_stage.qualified_team_ids)
    for team_id in group_stage.qualified_team_ids:
        qualified[team_index[team_id]] = True
    for team_id in group_stage.top_two_qualifiers:
        top_two[team_index[team_id]] = True
    for row in group_stage.third_place_rankings:
        third_finish[team_index[row.team_id]] = True
    for team_id in group_stage.third_place_qualifiers:
        third_qualified[team_index[team_id]] = True
    for table in group_stage.group_tables.values():
        for row in table:
            points[team_index[row.team_id]] = min(int(row.points), 255)

    for team in config.teams:
        team_idx = team_index[team.id]
        if team.id not in qualified_ids:
            max_stage[team_idx] = 0
            continue
        elimination_stage = knockout.eliminated_stage_by_team[team.id]
        summary_stage = ELIMINATION_STAGE_TO_SUMMARY_STAGE[elimination_stage]
        max_stage[team_idx] = STAGES.index(summary_stage)

    qualifier_order = np.full(QUALIFIER_COUNT, -1, dtype=np.int16)
    for index, team_id in enumerate(group_stage.qualified_team_ids):
        qualifier_order[index] = team_index[team_id]

    knockout_opponents = np.full(
        (team_count, len(ROUND_NAMES)),
        -1,
        dtype=np.int16,
    )
    for team in config.teams:
        if team.id not in qualified_ids:
            continue
        team_idx = team_index[team.id]
        for stage_index, stage in enumerate(ROUND_NAMES):
            match = next(
                (
                    candidate
                    for candidate in knockout.rounds[stage]
                    if team.id in {candidate.team_a_id, candidate.team_b_id}
                ),
                None,
            )
            if match is None:
                continue
            opponent_id = (
                match.team_b_id
                if match.team_a_id == team.id
                else match.team_a_id
            )
            knockout_opponents[team_idx, stage_index] = team_index[opponent_id]
            if match.winner_team_id != team.id:
                break

    champion_idx = team_index[knockout.champion_team_id]
    return (
        champion_idx,
        qualified,
        top_two,
        third_finish,
        third_qualified,
        points,
        max_stage,
        qualifier_order,
        knockout_opponents,
    )


def run_simulation_batch(
    config: TournamentConfig,
    match_model: MatchModel,
    *,
    master_seed: int,
    batch_index: int,
    batch_size: int,
    team_index: dict[str, int],
) -> SimulationBatchTrace:
    """Run one batch and return trace arrays."""
    from app.simulation.seed_sequence import SeedSequence

    team_count = len(team_index)
    sequence = SeedSequence(master_seed)
    champions = np.empty(batch_size, dtype=np.int16)
    qualified = np.empty((batch_size, team_count), dtype=np.bool_)
    top_two = np.empty((batch_size, team_count), dtype=np.bool_)
    third_finish = np.empty((batch_size, team_count), dtype=np.bool_)
    third_qualified = np.empty((batch_size, team_count), dtype=np.bool_)
    points = np.empty((batch_size, team_count), dtype=np.uint8)
    max_stage = np.empty((batch_size, team_count), dtype=np.uint8)
    qualifier_order = np.empty((batch_size, QUALIFIER_COUNT), dtype=np.int16)
    knockout_opponents = np.empty((batch_size, team_count, len(ROUND_NAMES)), dtype=np.int16)

    for simulation_index in range(batch_size):
        seed = sequence.child_seed(batch_index, simulation_index)
        (
            champion_idx,
            qualification_mask,
            top_two_mask,
            third_finish_mask,
            third_qualified_mask,
            points_row,
            max_stage_row,
            qualifier_order_row,
            knockout_opponents_row,
        ) = run_simulation_trace(config, match_model, seed, team_index)
        champions[simulation_index] = champion_idx
        qualified[simulation_index] = qualification_mask
        top_two[simulation_index] = top_two_mask
        third_finish[simulation_index] = third_finish_mask
        third_qualified[simulation_index] = third_qualified_mask
        points[simulation_index] = points_row
        max_stage[simulation_index] = max_stage_row
        qualifier_order[simulation_index] = qualifier_order_row
        knockout_opponents[simulation_index] = knockout_opponents_row

    return SimulationBatchTrace(
        champions=champions,
        qualified=qualified,
        top_two=top_two,
        third_finish=third_finish,
        third_qualified=third_qualified,
        points=points,
        max_stage=max_stage,
        qualifier_order=qualifier_order,
        knockout_opponents=knockout_opponents,
    )

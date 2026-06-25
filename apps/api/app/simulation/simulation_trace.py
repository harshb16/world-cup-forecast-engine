"""Compact single-tournament simulation traces for bank storage."""

from __future__ import annotations

import numpy as np

from app.models.domain import TournamentConfig
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import simulate_knockout
from app.simulation.match_models import MatchModel


def run_simulation_trace(
    config: TournamentConfig,
    match_model: MatchModel,
    seed: int,
    team_index: dict[str, int],
) -> tuple[int, np.ndarray]:
    """Return champion index and qualification bitmask for one simulation."""
    rng = np.random.default_rng(seed)
    teams_by_id = {team.id: team for team in config.teams}
    group_stage = simulate_group_stage(config, match_model, rng)
    knockout = simulate_knockout(
        group_stage.qualified_team_ids,
        teams_by_id,
        match_model,
        rng,
    )
    qualified = np.zeros(len(team_index), dtype=np.bool_)
    for team_id in group_stage.qualified_team_ids:
        qualified[team_index[team_id]] = True
    champion_idx = team_index[knockout.champion_team_id]
    return champion_idx, qualified


def run_simulation_batch(
    config: TournamentConfig,
    match_model: MatchModel,
    *,
    master_seed: int,
    batch_index: int,
    batch_size: int,
    team_index: dict[str, int],
) -> tuple[np.ndarray, np.ndarray]:
    """Run one batch and return champion and qualification arrays."""
    from app.simulation.seed_sequence import SeedSequence

    sequence = SeedSequence(master_seed)
    champions = np.empty(batch_size, dtype=np.int16)
    qualified = np.empty((batch_size, len(team_index)), dtype=np.bool_)
    for simulation_index in range(batch_size):
        seed = sequence.child_seed(batch_index, simulation_index)
        champion_idx, qualification_mask = run_simulation_trace(
            config,
            match_model,
            seed,
            team_index,
        )
        champions[simulation_index] = champion_idx
        qualified[simulation_index] = qualification_mask
    return champions, qualified

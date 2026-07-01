"""Head-to-head meeting probability between two teams."""

from collections import Counter
from pathlib import Path

import numpy as np

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.schemas import HeadToHeadResponse
from app.services.bracket_materialization_service import is_group_stage_complete
from app.services.data_loader import load_tournament
from app.services.simulation_bank_service import load_bank_arrays
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

    bank_path = _resolve_bank_path()
    if is_group_stage_complete(config) and bank_path is not None:
        return calculate_head_to_head_from_bank(
            bank_path,
            team_a_id,
            team_b_id,
            data_mode,
            model_type=model_type,
        )

    return _calculate_head_to_head_live(
        team_a_id,
        team_b_id,
        data_mode,
        model_type=model_type,
        n_simulations=n_simulations,
        seed=seed,
    )


def calculate_head_to_head_from_bank(
    bank_path: Path,
    team_a_id: str,
    team_b_id: str,
    data_mode: str,
    model_type: str = DEFAULT_MODEL_TYPE,
) -> HeadToHeadResponse:
    """Derive meeting probabilities from stored knockout opponent traces."""
    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
    if team_a_id not in teams_by_id or team_b_id not in teams_by_id:
        raise ValueError("unknown team_id")

    bank = load_bank_arrays(bank_path)
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    knockout_opponents: np.ndarray = bank["knockout_opponents"]  # type: ignore[assignment]
    n_simulations: int = bank["n_simulations"]  # type: ignore[assignment]
    team_a_index = team_ids.index(team_a_id)
    team_b_index = team_ids.index(team_b_id)

    meeting_counts: Counter[str] = Counter()
    for stage_index, stage in enumerate(ROUND_NAMES):
        met = (
            knockout_opponents[:, team_a_index, stage_index] == team_b_index
        ) & (knockout_opponents[:, team_b_index, stage_index] == team_a_index)
        meeting_counts[stage] = int(np.sum(met))

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


def _calculate_head_to_head_live(
    team_a_id: str,
    team_b_id: str,
    data_mode: str,
    *,
    model_type: str = DEFAULT_MODEL_TYPE,
    n_simulations: int = 500,
    seed: int = 42,
) -> HeadToHeadResponse:
    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
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


def _resolve_bank_path() -> Path | None:
    from app.services.runtime_store import get_active_forecast_bank_path

    bank_path = get_active_forecast_bank_path()
    if bank_path is not None and bank_path.exists():
        return bank_path
    return None

"""Team path explorer service."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np

from app.core.config import BOOTSTRAP_PROCESSED_DIR, DEFAULT_MODEL_TYPE
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
from app.services.simulation_bank_service import load_bank_arrays
from app.services.simulation_service import create_match_model
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import ROUND_NAMES, simulate_knockout

TEAM_PATHS_FILENAME = "team_paths.json"
BOOTSTRAP_TEAM_PATHS_PATH = BOOTSTRAP_PROCESSED_DIR / TEAM_PATHS_FILENAME


def calculate_team_path(
    request: TeamPathRequest,
    data_mode: str,
) -> TeamPathResponse:
    """Calculate likely knockout opponents for one team via live Monte Carlo."""
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
            _build_live_stage_response(
                stage,
                reached_counts[stage],
                opponent_counts[stage],
                teams_by_id,
                request.n_simulations,
            )
            for stage in ROUND_NAMES
        ],
    )


def team_path_from_bank(
    bank_path: Path,
    team_id: str,
    data_mode: str,
    *,
    model_type: str = DEFAULT_MODEL_TYPE,
    seed: int | None = None,
) -> TeamPathResponse:
    """Derive one team's knockout path from a stored simulation bank."""
    bank = load_bank_arrays(bank_path)
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    if team_id not in team_ids:
        raise ValueError(f"unknown team_id: {team_id}")

    if seed is None:
        payload = np.load(bank_path, allow_pickle=True)
        seed = int(payload["master_seed"])

    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
    team_index = team_ids.index(team_id)
    n_simulations: int = bank["n_simulations"]  # type: ignore[assignment]
    knockout_opponents: np.ndarray = bank["knockout_opponents"]  # type: ignore[assignment]

    metadata = SimulationMetadataResponse(
        n_simulations=n_simulations,
        model_type=model_type,
        seed=seed,
        **load_metadata(data_mode),
    )
    team = teams_by_id[team_id]

    return TeamPathResponse(
        metadata=metadata,
        team=BracketTeamResponse(
            team_id=team.id,
            team_name=team.name,
            group_id=team.group_id,
            rating=team.rating,
        ),
        stages=[
            _build_bank_stage_response(
                stage,
                knockout_opponents[:, team_index, stage_index],
                teams_by_id,
                team_ids,
                n_simulations,
            )
            for stage_index, stage in enumerate(ROUND_NAMES)
        ],
    )


def all_team_paths_from_bank(
    bank_path: Path,
    data_mode: str,
    *,
    model_type: str = DEFAULT_MODEL_TYPE,
    seed: int | None = None,
) -> dict[str, TeamPathResponse]:
    """Derive knockout paths for every team in a stored simulation bank."""
    bank = load_bank_arrays(bank_path)
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    return {
        team_id: team_path_from_bank(
            bank_path,
            team_id,
            data_mode,
            model_type=model_type,
            seed=seed,
        )
        for team_id in team_ids
    }


def serialize_team_paths(
    team_paths: dict[str, TeamPathResponse],
) -> dict[str, dict[str, object]]:
    """Serialize team path responses for JSON sidecar storage."""
    return {
        team_id: response.model_dump(mode="json")
        for team_id, response in team_paths.items()
    }


def write_team_paths_sidecar(
    target_dir: Path,
    team_paths: dict[str, TeamPathResponse],
) -> Path:
    """Write precomputed team paths next to a forecast snapshot payload."""
    target_dir.mkdir(parents=True, exist_ok=True)
    cache_path = target_dir / TEAM_PATHS_FILENAME
    cache_path.write_text(
        json.dumps(serialize_team_paths(team_paths), indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    return cache_path


def load_team_paths_sidecar(cache_path: Path) -> dict[str, TeamPathResponse]:
    """Load precomputed team paths from a JSON sidecar file."""
    payload = json.loads(cache_path.read_text(encoding="utf-8"))
    return {
        team_id: TeamPathResponse.model_validate(team_path)
        for team_id, team_path in payload.items()
    }


def load_published_team_path(
    team_id: str,
    *,
    cache_path: Path | None = None,
    bank_path: Path | None = None,
    data_mode: str = "processed",
    model_type: str = DEFAULT_MODEL_TYPE,
) -> TeamPathResponse:
    """Load a published team path from cache, falling back to bank aggregation."""
    if cache_path is not None and cache_path.exists():
        team_paths = load_team_paths_sidecar(cache_path)
        if team_id in team_paths:
            return team_paths[team_id]
        raise ValueError(f"unknown team_id: {team_id}")

    if bank_path is not None and bank_path.exists():
        return team_path_from_bank(
            bank_path,
            team_id,
            data_mode,
            model_type=model_type,
        )

    raise FileNotFoundError(
        "Team path is unavailable. Publish a forecast snapshot with a simulation bank."
    )


def get_published_team_path(team_id: str, data_mode: str) -> TeamPathResponse:
    """Load the active forecast's bank-derived team path for one team."""
    from app.services.forecast_snapshot_service import load_forecast_snapshot
    from app.services.runtime_store import (
        get_active_forecast_bank_path,
        get_active_forecast_directory,
    )

    cache_path: Path | None = None
    forecast_dir = get_active_forecast_directory()
    if forecast_dir is not None:
        candidate = forecast_dir / TEAM_PATHS_FILENAME
        if candidate.exists():
            cache_path = candidate
    if cache_path is None and BOOTSTRAP_TEAM_PATHS_PATH.exists():
        cache_path = BOOTSTRAP_TEAM_PATHS_PATH

    snapshot = load_forecast_snapshot()
    return load_published_team_path(
        team_id,
        cache_path=cache_path,
        bank_path=get_active_forecast_bank_path(),
        data_mode=data_mode,
        model_type=snapshot.model_version,
    )


def _build_live_stage_response(
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


def _build_bank_stage_response(
    stage: str,
    opponent_indices: np.ndarray,
    teams_by_id: dict[str, object],
    team_ids: list[str],
    n_simulations: int,
) -> TeamPathStageResponse:
    played_mask = opponent_indices >= 0
    reached_count = int(np.sum(played_mask))
    opponent_counter: Counter[str] = Counter()
    if reached_count > 0:
        for opponent_index in opponent_indices[played_mask]:
            opponent_counter[team_ids[int(opponent_index)]] += 1

    opponents = [
        TeamPathOpponentResponse(
            team_id=opponent_id,
            team_name=teams_by_id[opponent_id].name,
            count=count,
            probability=count / reached_count if reached_count else 0.0,
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

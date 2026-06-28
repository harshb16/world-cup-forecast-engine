"""Build and persist NumPy simulation banks for forecast snapshots."""

from __future__ import annotations

import hashlib
import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.domain import SimulationSummary
from app.models.schemas import (
    ModelType,
    SimulationMetadataResponse,
    SimulationSummaryResponse,
    ThirdPlaceSlotDistributionResponse,
    ThirdPlaceTeamResponse,
    ThirdPlaceTrackerResponse,
)
from app.services.data_loader import load_metadata, load_tournament
from app.services.runtime_store import get_runtime_root
from app.services.sync_scheduler_service import is_tournament_active
from app.simulation.group_table import calculate_group_table
from app.simulation.knockout import WorldCup2026BracketBuilder
from app.simulation.monte_carlo import STAGES
from app.simulation.simulation_trace import SimulationBatchTrace, run_simulation_batch

BASELINE_SIMULATIONS = 100_000
IN_PLAY_SIMULATIONS = 30_000
DIAGNOSTIC_SIMULATION_CAP = 1_000
DEFAULT_BATCH_SIZE = 2_500


def build_snapshot_seed(
    *,
    data_version: str | None,
    model_version: str,
) -> int:
    """Return deterministic master seed from data and model versions."""
    payload = f"{data_version or 'unknown'}:{model_version}"
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def recommended_bank_size() -> int:
    """Return baseline or in-play bank size based on tournament activity."""
    override = os.getenv("WCO_SNAPSHOT_SIMULATIONS")
    if override:
        return max(1, int(override))
    return IN_PLAY_SIMULATIONS if is_tournament_active() else BASELINE_SIMULATIONS


def _batch_worker(payload: tuple) -> SimulationBatchTrace:
    (
        config,
        model_type,
        data_mode,
        master_seed,
        batch_index,
        batch_size,
        team_index,
    ) = payload
    from app.services.simulation_service import create_match_model

    match_model = create_match_model(model_type, data_mode)
    return run_simulation_batch(
        config,
        match_model,
        master_seed=master_seed,
        batch_index=batch_index,
        batch_size=batch_size,
        team_index=team_index,
    )


def _concat_batches(parts: list[SimulationBatchTrace]) -> SimulationBatchTrace:
    return SimulationBatchTrace(
        champions=np.concatenate([part.champions for part in parts]),
        qualified=np.concatenate([part.qualified for part in parts], axis=0),
        top_two=np.concatenate([part.top_two for part in parts], axis=0),
        third_finish=np.concatenate([part.third_finish for part in parts], axis=0),
        third_qualified=np.concatenate([part.third_qualified for part in parts], axis=0),
        points=np.concatenate([part.points for part in parts], axis=0),
        max_stage=np.concatenate([part.max_stage for part in parts], axis=0),
        qualifier_order=np.concatenate([part.qualifier_order for part in parts], axis=0),
        knockout_opponents=np.concatenate([part.knockout_opponents for part in parts], axis=0),
    )


def build_simulation_bank(
    *,
    data_mode: str = "processed",
    model_type: str = DEFAULT_MODEL_TYPE,
    data_version: str | None,
    n_simulations: int | None = None,
    master_seed: int | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_workers: int | None = None,
) -> tuple[Path, dict[str, object]]:
    """Run parallel simulation batches and persist one `.npz` bank."""
    config = load_tournament(data_mode)
    team_ids = [team.id for team in config.teams]
    team_index = {team_id: index for index, team_id in enumerate(team_ids)}
    total = n_simulations or recommended_bank_size()
    seed = master_seed if master_seed is not None else build_snapshot_seed(
        data_version=data_version,
        model_version=model_type,
    )
    workers = max_workers or min(4, max(1, os.cpu_count() or 1))
    batches = []
    remaining = total
    batch_index = 0
    while remaining > 0:
        size = min(batch_size, remaining)
        batches.append((batch_index, size))
        remaining -= size
        batch_index += 1

    batch_parts: list[SimulationBatchTrace] = []
    payloads = [
        (
            config,
            model_type,
            data_mode,
            seed,
            index,
            size,
            team_index,
        )
        for index, size in batches
    ]

    if workers == 1 or len(payloads) == 1:
        for payload in payloads:
            batch_parts.append(_batch_worker(payload))
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for trace in executor.map(_batch_worker, payloads):
                batch_parts.append(trace)

    trace = _concat_batches(batch_parts)
    target_dir = get_runtime_root() / "banks"
    target_dir.mkdir(parents=True, exist_ok=True)
    bank_path = target_dir / f"bank-{seed}-{total}.npz"
    np.savez_compressed(
        bank_path,
        team_ids=np.array(team_ids, dtype=object),
        champions=trace.champions,
        qualified=trace.qualified,
        top_two=trace.top_two,
        third_finish=trace.third_finish,
        third_qualified=trace.third_qualified,
        points=trace.points,
        max_stage=trace.max_stage,
        qualifier_order=trace.qualifier_order,
        knockout_opponents=trace.knockout_opponents,
        master_seed=np.int64(seed),
        n_simulations=np.int32(total),
        model_version=np.array(model_type),
        data_version=np.array(data_version or "unknown"),
    )
    metadata = {
        "bank_path": bank_path,
        "master_seed": seed,
        "n_simulations": total,
        "model_version": model_type,
        "data_version": data_version,
    }
    return bank_path, metadata


def load_bank_arrays(bank_path: Path) -> dict[str, np.ndarray | list[str] | int]:
    """Load simulation bank arrays and metadata."""
    payload = np.load(bank_path, allow_pickle=True)
    team_ids = [str(team_id) for team_id in payload["team_ids"].tolist()]
    n_simulations = int(payload["n_simulations"])
    return {
        "team_ids": team_ids,
        "n_simulations": n_simulations,
        "champions": payload["champions"],
        "qualified": payload["qualified"],
        "top_two": payload["top_two"],
        "third_finish": payload["third_finish"],
        "third_qualified": payload["third_qualified"],
        "points": payload["points"],
        "max_stage": payload["max_stage"],
        "qualifier_order": payload["qualifier_order"],
        "knockout_opponents": payload["knockout_opponents"],
    }


def simulation_summary_from_bank(bank_path: Path) -> SimulationSummary:
    """Aggregate tournament simulation summary from a stored bank."""
    bank = load_bank_arrays(bank_path)
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    n_simulations: int = bank["n_simulations"]  # type: ignore[assignment]
    max_stage: np.ndarray = bank["max_stage"]  # type: ignore[assignment]
    qualified: np.ndarray = bank["qualified"]  # type: ignore[assignment]
    top_two: np.ndarray = bank["top_two"]  # type: ignore[assignment]
    third_finish: np.ndarray = bank["third_finish"]  # type: ignore[assignment]
    third_qualified: np.ndarray = bank["third_qualified"]  # type: ignore[assignment]
    points: np.ndarray = bank["points"]  # type: ignore[assignment]

    stage_probabilities: dict[str, dict[str, float]] = {}
    for team_index, team_id in enumerate(team_ids):
        team_stages = max_stage[:, team_index]
        stage_probabilities[team_id] = {
            stage: float(np.mean(team_stages == stage_index))
            for stage_index, stage in enumerate(STAGES)
        }

    return SimulationSummary(
        stage_probabilities=stage_probabilities,
        average_points_by_team={
            team_id: float(np.mean(points[:, team_index]))
            for team_index, team_id in enumerate(team_ids)
        },
        group_qualification_probability={
            team_id: float(np.mean(qualified[:, team_index]))
            for team_index, team_id in enumerate(team_ids)
        },
        top_two_probability={
            team_id: float(np.mean(top_two[:, team_index]))
            for team_index, team_id in enumerate(team_ids)
        },
        third_place_finish_probability={
            team_id: float(np.mean(third_finish[:, team_index]))
            for team_index, team_id in enumerate(team_ids)
        },
        third_place_qualification_probability={
            team_id: float(np.mean(third_qualified[:, team_index]))
            for team_index, team_id in enumerate(team_ids)
        },
    )


def champion_probabilities_from_bank(bank_path: Path) -> dict[str, float]:
    """Aggregate champion probabilities from a stored simulation bank."""
    bank = load_bank_arrays(bank_path)
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    champions: np.ndarray = bank["champions"]  # type: ignore[assignment]
    counts = np.bincount(champions, minlength=len(team_ids))
    total = int(counts.sum())
    return {
        team_id: float(count / total)
        for team_id, count in zip(team_ids, counts, strict=True)
        if count > 0
    }


def simulation_summary_response_from_bank(
    bank_path: Path,
    *,
    data_mode: str,
    model_type: ModelType,
    seed: int,
) -> SimulationSummaryResponse:
    """Build API summary response from a stored simulation bank."""
    from app.services.simulation_service import _to_response

    bank = load_bank_arrays(bank_path)
    summary = simulation_summary_from_bank(bank_path)
    teams = load_tournament(data_mode).teams
    metadata = SimulationMetadataResponse(
        n_simulations=int(bank["n_simulations"]),  # type: ignore[arg-type]
        model_type=model_type,
        seed=seed,
        overrides_applied=[],
        **load_metadata(data_mode),
    )
    return _to_response(summary, teams, metadata)


def third_place_tracker_from_bank(
    bank_path: Path,
    data_mode: str,
    model_type: ModelType = DEFAULT_MODEL_TYPE,
) -> ThirdPlaceTrackerResponse:
    """Build third-place tracker response from a stored simulation bank."""
    bank = load_bank_arrays(bank_path)
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    n_simulations: int = bank["n_simulations"]  # type: ignore[assignment]
    third_qualified: np.ndarray = bank["third_qualified"]  # type: ignore[assignment]
    third_finish: np.ndarray = bank["third_finish"]  # type: ignore[assignment]
    points: np.ndarray = bank["points"]  # type: ignore[assignment]
    qualifier_order: np.ndarray = bank["qualifier_order"]  # type: ignore[assignment]

    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
    builder = WorldCup2026BracketBuilder()
    group_matches = [match for match in config.matches if match.stage == "group"]
    current_tables = {
        group.id: {
            row.team_id: row.points
            for row in calculate_group_table(group, teams_by_id, group_matches)
        }
        for group in config.groups
    }

    qualification_counts: Counter[str] = Counter()
    slot_counts: dict[str, Counter[str]] = {}
    points_samples: dict[str, list[float]] = {}

    for simulation_index in range(n_simulations):
        for team_index, team_id in enumerate(team_ids):
            if third_qualified[simulation_index, team_index]:
                qualification_counts[team_id] += 1
            if third_finish[simulation_index, team_index]:
                points_samples.setdefault(team_id, []).append(
                    float(points[simulation_index, team_index])
                )

        qualified_team_ids = [
            team_ids[int(team_index)]
            for team_index in qualifier_order[simulation_index]
            if int(team_index) >= 0
        ]
        if len(qualified_team_ids) != 32:
            continue
        try:
            pairs = builder.build_round_of_32(qualified_team_ids, teams_by_id)
        except ValueError:
            continue
        third_qualifier_ids = {
            team_ids[int(team_index)]
            for team_index, _ in enumerate(team_ids)
            if third_qualified[simulation_index, team_index]
        }
        for index, (team_a_id, team_b_id) in enumerate(pairs, start=1):
            slot_label = f"R32-{index:02d}"
            for team_id in (team_a_id, team_b_id):
                if team_id in third_qualifier_ids:
                    slot_counts.setdefault(team_id, Counter())[slot_label] += 1

    tracked_team_ids = {
        team_id for team_id, count in qualification_counts.items() if count > 0
    }
    teams = []
    for team_id in sorted(
        tracked_team_ids,
        key=lambda team: qualification_counts.get(team, 0),
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


def champion_probabilities_match_summary(
    summary: SimulationSummaryResponse,
    *,
    tolerance: float = 1e-9,
) -> bool:
    """Return whether champion dict matches per-team champion stage probabilities."""
    for team in summary.teams:
        champion_probability = summary.champion_probabilities.get(team.team_id, 0.0)
        if abs(champion_probability - team.champion) > tolerance:
            return False
    return True

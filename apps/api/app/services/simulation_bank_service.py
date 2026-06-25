"""Build and persist NumPy simulation banks for forecast snapshots."""

from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from app.core.config import DEFAULT_MODEL_TYPE
from app.services.data_loader import load_tournament
from app.services.runtime_store import get_runtime_root
from app.services.sync_scheduler_service import is_tournament_active
from app.simulation.simulation_trace import run_simulation_batch

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


def _batch_worker(payload: tuple) -> tuple[np.ndarray, np.ndarray]:
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

    champion_parts: list[np.ndarray] = []
    qualified_parts: list[np.ndarray] = []
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
            champions, qualified = _batch_worker(payload)
            champion_parts.append(champions)
            qualified_parts.append(qualified)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for champions, qualified in executor.map(_batch_worker, payloads):
                champion_parts.append(champions)
                qualified_parts.append(qualified)

    champions = np.concatenate(champion_parts)
    qualified = np.concatenate(qualified_parts, axis=0)
    target_dir = get_runtime_root() / "banks"
    target_dir.mkdir(parents=True, exist_ok=True)
    bank_path = target_dir / f"bank-{seed}-{total}.npz"
    np.savez_compressed(
        bank_path,
        team_ids=np.array(team_ids, dtype=object),
        champions=champions,
        qualified=qualified,
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


def champion_probabilities_from_bank(bank_path: Path) -> dict[str, float]:
    """Aggregate champion probabilities from a stored simulation bank."""
    payload = np.load(bank_path, allow_pickle=True)
    team_ids = [str(team_id) for team_id in payload["team_ids"].tolist()]
    champions = payload["champions"]
    counts = np.bincount(champions, minlength=len(team_ids))
    total = int(counts.sum())
    return {
        team_id: float(count / total)
        for team_id, count in zip(team_ids, counts, strict=True)
        if count > 0
    }

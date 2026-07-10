"""Offline deterministic time-machine artifact generator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.schemas import (
    ProbabilityMoverResponse,
    ProbabilityMoversResponse,
    TimeMachineManifestResponse,
    TimeMachineProvenanceResponse,
    TimeMachineSnapshotResponse,
)
from app.services.data_loader import load_metadata, load_tournament
from app.services.forecast_snapshot_service import build_forecast_snapshot_from_bank
from app.services.simulation_bank_service import build_simulation_bank
from app.services.team_path_service import all_team_paths_from_bank, serialize_team_paths
from app.services.time_machine_service import (
    TIME_MACHINE_BANK_FILENAME,
    TIME_MACHINE_MANIFEST_FILENAME,
    TIME_MACHINE_SNAPSHOT_FILENAME,
    TIME_MACHINE_TEAM_PATHS_FILENAME,
    derive_time_machine_seed,
    get_time_machine_root,
    load_raw_fixture_index,
    milestone_catalog,
    slice_tournament_at_milestone,
)
from app.simulation.group_table import calculate_group_table

DEFAULT_TIME_MACHINE_SIMULATIONS = 100_000


def generate_time_machine_artifacts(
    *,
    n_simulations: int | None = None,
    force: bool = False,
    require_complete: bool = False,
    target_root: Path | None = None,
    data_mode: str = "processed",
    model_version: str = DEFAULT_MODEL_TYPE,
    progress: bool = True,
) -> TimeMachineManifestResponse:
    """Build available replay banks and JSON sidecars with resumable writes."""
    total = n_simulations or int(
        os.getenv("WCO_TIME_MACHINE_SIMULATIONS", str(DEFAULT_TIME_MACHINE_SIMULATIONS))
    )
    if total < 1:
        raise ValueError("simulation count must be at least 1")

    config = load_tournament(data_mode)
    raw_fixtures = load_raw_fixture_index()
    metadata = load_metadata(data_mode)
    data_version = str(metadata.get("data_version") or "unknown")
    catalog = milestone_catalog(config, raw_fixtures)
    unavailable = [item.id for item in catalog if not item.available]
    if require_complete and unavailable:
        raise RuntimeError(f"incomplete tournament milestones: {', '.join(unavailable)}")

    root = target_root or get_time_machine_root()
    root.mkdir(parents=True, exist_ok=True)
    existing = _read_json(root / TIME_MACHINE_MANIFEST_FILENAME)
    existing_by_id = {
        str(item.get("id")): item for item in existing.get("milestones", [])
    } if existing else {}
    generated_at = str(metadata.get("last_updated") or "1970-01-01T00:00:00+00:00")
    previous_probabilities: dict[str, float] | None = None
    completed_catalog = []

    for milestone in catalog:
        if not milestone.available:
            completed_catalog.append(milestone)
            continue
        seed = derive_time_machine_seed(data_version, model_version, milestone.id)
        fingerprint = _fingerprint(data_version, model_version, milestone.id, seed, total)
        milestone_dir = root / "milestones" / milestone.id
        snapshot_path = milestone_dir / TIME_MACHINE_SNAPSHOT_FILENAME
        team_paths_path = milestone_dir / TIME_MACHINE_TEAM_PATHS_FILENAME
        bank_path = milestone_dir / TIME_MACHINE_BANK_FILENAME
        previous_entry = existing_by_id.get(milestone.id, {})

        if (
            not force
            and previous_entry.get("fingerprint") == fingerprint
            and all(path.exists() for path in (snapshot_path, team_paths_path, bank_path))
        ):
            if progress:
                print(f"[{milestone.order + 1}/9] {milestone.id}: resume")
            snapshot = TimeMachineSnapshotResponse.model_validate_json(
                snapshot_path.read_text(encoding="utf-8")
            )
            previous_probabilities = snapshot.forecast.summary.champion_probabilities
            completed_catalog.append(milestone.model_copy(update=previous_entry))
            continue

        if progress:
            print(f"[{milestone.order + 1}/9] {milestone.id}: {total:,} simulations")
        milestone_dir.mkdir(parents=True, exist_ok=True)
        sliced = slice_tournament_at_milestone(config, raw_fixtures, milestone.id)
        temp_bank = milestone_dir / ".bank.tmp.npz"
        built_bank, bank_meta = build_simulation_bank(
            data_mode=data_mode,
            model_type=model_version,
            data_version=data_version,
            n_simulations=total,
            master_seed=seed,
            config=sliced,
            target_path=temp_bank,
        )
        built_bank.replace(bank_path)
        forecast = build_forecast_snapshot_from_bank(
            bank_path,
            bank_meta,
            data_mode,
            config=sliced,
            generated_at=generated_at,
        )
        forecast = forecast.model_copy(
            update={
                "summary": forecast.summary.model_copy(
                    update={
                        "metadata": forecast.summary.metadata.model_copy(
                            update={
                                "completed_result_count": milestone.known_result_count,
                                "last_updated": generated_at,
                            }
                        )
                    }
                )
            }
        )
        movers = _probability_movers(
            previous_probabilities,
            forecast.summary.champion_probabilities,
            {team.id: team.name for team in sliced.teams},
            milestone.previous_id,
            milestone.id,
        )
        teams_by_id = {team.id: team for team in sliced.teams}
        group_matches = [match for match in sliced.matches if match.stage == "group"]
        group_tables = {
            group.id: [
                row.model_dump(mode="json")
                for row in calculate_group_table(group, teams_by_id, group_matches)
            ]
            for group in sliced.groups
        }
        snapshot = TimeMachineSnapshotResponse(
            milestone=milestone.model_copy(
                update={"seed": seed, "simulation_count": total, "fingerprint": fingerprint}
            ),
            provenance=TimeMachineProvenanceResponse(
                data_version=data_version,
                model_version=model_version,
                seed=seed,
                simulation_count=total,
                generated_at=generated_at,
            ),
            forecast=forecast,
            group_tables=group_tables,
            fixtures=[match.model_dump(mode="json") for match in sliced.matches],
            movers=movers,
        )
        _write_json_atomic(snapshot_path, snapshot.model_dump(mode="json"))
        team_paths = all_team_paths_from_bank(
            bank_path,
            data_mode,
            model_type=model_version,
            seed=seed,
            config=sliced,
        )
        _write_json_atomic(team_paths_path, serialize_team_paths(team_paths))
        artifact_size = sum(path.stat().st_size for path in (snapshot_path, team_paths_path, bank_path))
        checksum = _combined_checksum(snapshot_path, team_paths_path, bank_path)
        completed_catalog.append(
            milestone.model_copy(
                update={
                    "seed": seed,
                    "simulation_count": total,
                    "artifact_size_bytes": artifact_size,
                    "checksum": checksum,
                    "fingerprint": fingerprint,
                }
            )
        )
        previous_probabilities = forecast.summary.champion_probabilities

    manifest = TimeMachineManifestResponse(
        archive_mode=metadata.get("archive_mode"),
        data_version=data_version,
        model_version=model_version,
        generated_at=generated_at,
        simulation_count=total,
        milestones=completed_catalog,
    )
    _write_json_atomic(root / TIME_MACHINE_MANIFEST_FILENAME, manifest.model_dump(mode="json"))
    return manifest


def _probability_movers(
    previous: dict[str, float] | None,
    current: dict[str, float],
    names: dict[str, str],
    previous_id: str | None,
    current_id: str,
) -> ProbabilityMoversResponse:
    rows = [
        ProbabilityMoverResponse(
            team_id=team_id,
            team_name=names.get(team_id, team_id),
            previous_probability=(previous or current).get(team_id, 0.0),
            current_probability=probability,
            delta=probability - (previous or current).get(team_id, 0.0),
        )
        for team_id, probability in current.items()
    ]
    return ProbabilityMoversResponse(
        risers=sorted(rows, key=lambda row: row.delta, reverse=True)[:8],
        fallers=sorted(rows, key=lambda row: row.delta)[:8],
        previous_timestamp=previous_id,
        current_timestamp=current_id,
    )


def _fingerprint(data_version: str, model_version: str, milestone_id: str, seed: int, total: int) -> str:
    return hashlib.sha256(
        f"{data_version}:{model_version}:{milestone_id}:{seed}:{total}".encode()
    ).hexdigest()


def _combined_checksum(*paths: Path) -> str:
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulations", type=int)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    generate_time_machine_artifacts(
        n_simulations=args.simulations,
        force=args.force,
        require_complete=args.require_complete,
    )


if __name__ == "__main__":
    main()

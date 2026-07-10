"""Tournament replay milestone catalog, slicing, and artifact reads."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.core.archive_config import get_archive_data_dir
from app.core.config import DEFAULT_MODEL_TYPE
from app.models.domain import Match, TournamentConfig
from app.models.schemas import (
    ProbabilityHistoryResponse,
    ProbabilitySnapshotResponse,
    TeamPathResponse,
    TimeMachineManifestResponse,
    TimeMachineMilestoneResponse,
    TimeMachineSnapshotResponse,
)
from app.services.data_loader import get_processed_data_dir, load_metadata
from app.services.world_cup_schedule import group_matchday_for_date
from app.simulation.knockout import ROUND_NAMES

TIME_MACHINE_DIRNAME = "time_machine"
TIME_MACHINE_MANIFEST_FILENAME = "manifest.json"
TIME_MACHINE_SNAPSHOT_FILENAME = "snapshot.json"
TIME_MACHINE_TEAM_PATHS_FILENAME = "team_paths.json"
TIME_MACHINE_BANK_FILENAME = "bank.npz"


@dataclass(frozen=True)
class MilestoneDefinition:
    id: str
    label: str
    phase: str
    cutoff: str
    max_group_matchday: int
    knockout_through: str | None = None


MILESTONE_DEFINITIONS: tuple[MilestoneDefinition, ...] = (
    MilestoneDefinition("before_group_md1", "Before Matchday 1", "pre_tournament", "group_md0", 0),
    MilestoneDefinition("after_group_md1", "After Matchday 1", "group_stage", "group_md1", 1),
    MilestoneDefinition("after_group_md2", "After Matchday 2", "group_stage", "group_md2", 2),
    MilestoneDefinition("after_group_md3", "After Matchday 3", "group_stage", "group_md3", 3),
    MilestoneDefinition("after_round_of_32", "After Round of 32", "knockout", "Round of 32", 3, "Round of 32"),
    MilestoneDefinition("after_round_of_16", "After Round of 16", "knockout", "Round of 16", 3, "Round of 16"),
    MilestoneDefinition("after_quarter_finals", "After Quarter-finals", "knockout", "Quarter-finals", 3, "Quarter-finals"),
    MilestoneDefinition("after_semi_finals", "After Semi-finals", "knockout", "Semi-finals", 3, "Semi-finals"),
    MilestoneDefinition("after_final", "After Final", "complete", "Final", 3, "Final"),
)


def derive_time_machine_seed(
    data_version: str,
    model_version: str,
    milestone_id: str,
) -> int:
    """Derive a stable unsigned 32-bit seed from frozen replay inputs."""
    payload = f"{data_version}:{model_version}:{milestone_id}"
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:4], "big")


def milestone_catalog(
    config: TournamentConfig,
    raw_fixtures: dict[str, dict[str, Any]],
) -> list[TimeMachineMilestoneResponse]:
    """Return all nine milestones with complete-round availability."""
    availability = [_milestone_available(item, config, raw_fixtures) for item in MILESTONE_DEFINITIONS]
    catalog: list[TimeMachineMilestoneResponse] = []
    for index, (definition, available) in enumerate(zip(MILESTONE_DEFINITIONS, availability, strict=True)):
        sliced = slice_tournament_at_milestone(config, raw_fixtures, definition.id)
        catalog.append(
            TimeMachineMilestoneResponse(
                id=definition.id,
                label=definition.label,
                order=index,
                phase=definition.phase,  # type: ignore[arg-type]
                cutoff=definition.cutoff,
                known_result_count=sum(
                    match.result is not None and match.result.played
                    for match in sliced.matches
                ),
                available=available,
                previous_id=MILESTONE_DEFINITIONS[index - 1].id if index else None,
                next_id=MILESTONE_DEFINITIONS[index + 1].id if index + 1 < len(MILESTONE_DEFINITIONS) else None,
            )
        )
    return catalog


def slice_tournament_at_milestone(
    config: TournamentConfig,
    raw_fixtures: dict[str, dict[str, Any]],
    milestone_id: str,
) -> TournamentConfig:
    """Hide future results and remove future knockout pairings."""
    definition = get_milestone_definition(milestone_id)
    matches: list[Match] = []
    for match in config.matches:
        if match.stage == "group":
            reveal = _group_matchday(match.id, raw_fixtures) in range(1, definition.max_group_matchday + 1)
            matches.append(match if reveal else match.model_copy(update={"result": None, "winner_team_id": None}))
            continue

        if definition.knockout_through is None:
            continue
        if match.stage not in ROUND_NAMES:
            continue
        if ROUND_NAMES.index(match.stage) > ROUND_NAMES.index(definition.knockout_through):
            continue
        matches.append(match)

    return TournamentConfig(teams=config.teams, groups=config.groups, matches=matches)


def get_milestone_definition(milestone_id: str) -> MilestoneDefinition:
    for definition in MILESTONE_DEFINITIONS:
        if definition.id == milestone_id:
            return definition
    raise KeyError(milestone_id)


def get_time_machine_root() -> Path:
    archive_dir = get_archive_data_dir()
    return (archive_dir or get_processed_data_dir()) / TIME_MACHINE_DIRNAME


def load_time_machine_manifest() -> TimeMachineManifestResponse:
    path = get_time_machine_root() / TIME_MACHINE_MANIFEST_FILENAME
    if not path.exists():
        raise FileNotFoundError("Time-machine artifacts are missing. Run the offline generator.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    manifest = TimeMachineManifestResponse.model_validate(payload)
    active_data_version = str(load_metadata("processed").get("data_version") or "unknown")
    if manifest.data_version != active_data_version:
        raise RuntimeError("Time-machine artifacts are stale relative to the active archive.")
    return manifest


def load_time_machine_snapshot(milestone_id: str) -> TimeMachineSnapshotResponse:
    manifest = load_time_machine_manifest()
    milestone = next((item for item in manifest.milestones if item.id == milestone_id), None)
    if milestone is None or not milestone.available:
        raise KeyError(milestone_id)
    path = get_time_machine_root() / "milestones" / milestone_id / TIME_MACHINE_SNAPSHOT_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"Time-machine artifact is missing for {milestone_id}.")
    return TimeMachineSnapshotResponse.model_validate_json(path.read_text(encoding="utf-8"))


def load_time_machine_team_path(milestone_id: str, team_id: str) -> TeamPathResponse:
    """Load one team path from a milestone sidecar without simulation."""
    load_time_machine_snapshot(milestone_id)
    payload = json.loads(time_machine_team_paths_path(milestone_id).read_text(encoding="utf-8"))
    if team_id not in payload:
        raise KeyError(team_id)
    return TeamPathResponse.model_validate(payload[team_id])


def load_time_machine_probability_history() -> ProbabilityHistoryResponse:
    """Build chart-sized champion history from available snapshots."""
    manifest = load_time_machine_manifest()
    snapshots = []
    for milestone in manifest.milestones:
        if not milestone.available:
            continue
        snapshot = load_time_machine_snapshot(milestone.id)
        snapshots.append(
            ProbabilitySnapshotResponse(
                label=milestone.label,
                milestone_id=milestone.id,
                matchday=milestone.order if milestone.phase == "group_stage" else None,
                champion_probabilities=snapshot.forecast.summary.champion_probabilities,
            )
        )
    return ProbabilityHistoryResponse(snapshots=snapshots)


def time_machine_bank_path(milestone_id: str) -> Path:
    path = get_time_machine_root() / "milestones" / milestone_id / TIME_MACHINE_BANK_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"Time-machine bank is missing for {milestone_id}.")
    return path


def time_machine_team_paths_path(milestone_id: str) -> Path:
    path = get_time_machine_root() / "milestones" / milestone_id / TIME_MACHINE_TEAM_PATHS_FILENAME
    if not path.exists():
        raise FileNotFoundError(f"Time-machine team paths are missing for {milestone_id}.")
    return path


def _milestone_available(
    definition: MilestoneDefinition,
    config: TournamentConfig,
    raw_fixtures: dict[str, dict[str, Any]],
) -> bool:
    if definition.id == "before_group_md1":
        return True
    if definition.knockout_through is None:
        matches = [
            match for match in config.matches
            if match.stage == "group" and _group_matchday(match.id, raw_fixtures) == definition.max_group_matchday
        ]
        return bool(matches) and all(_played(match) for match in matches)
    matches = [match for match in config.matches if match.stage == definition.knockout_through]
    return bool(matches) and all(_played(match) and match.winner_team_id for match in matches)


def _played(match: Match) -> bool:
    return match.result is not None and match.result.played


def _group_matchday(match_id: str, raw_fixtures: dict[str, dict[str, Any]]) -> int | None:
    raw = raw_fixtures.get(match_id, {})
    value = raw.get("kickoff_utc") or raw.get("kickoff")
    if not value:
        return None
    try:
        match_date = datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            match_date = date.fromisoformat(str(value)[:10])
        except ValueError:
            return None
    return group_matchday_for_date(match_date)


def load_raw_fixture_index(path: Path | None = None) -> dict[str, dict[str, Any]]:
    fixture_path = path or (get_processed_data_dir() / "fixtures.json")
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    return {str(item["id"]): item for item in payload}

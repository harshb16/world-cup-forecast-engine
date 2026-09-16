"""Match-progress champion probability timeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.domain import Match, TournamentConfig
from app.models.schemas import (
    ModelType,
    ProbabilityHistoryResponse,
    ProbabilitySnapshotResponse,
)
from app.services.data_loader import SAMPLE_DATA_DIR, get_processed_data_dir, load_tournament
from app.services.simulation_service import create_match_model
from app.simulation.knockout import ROUND_NAMES
from app.simulation.monte_carlo import run_simulations
from app.services.world_cup_schedule import group_matchday_for_date

GROUP_MILESTONES: tuple[tuple[str, str, int], ...] = (
    ("before_group_md1", "Before Matchday 1", 0),
    ("after_group_md1", "After Matchday 1", 1),
    ("after_group_md2", "After Matchday 2", 2),
    ("after_group_md3", "After Matchday 3", 3),
)

KNOCKOUT_MILESTONE_PREFIX = "after_"


@dataclass(frozen=True)
class _Milestone:
    milestone_id: str
    label: str
    max_group_matchday: int
    knockout_through: str | None = None

    @property
    def matchday(self) -> int | None:
        if self.max_group_matchday <= 0:
            return None
        if self.knockout_through is not None:
            return None
        return self.max_group_matchday


def build_probability_timeline(
    data_mode: str,
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    n_simulations: int = 500,
    seed: int = 42,
) -> ProbabilityHistoryResponse:
    """Simulate champion odds at each tournament milestone."""
    config = load_tournament(data_mode)
    raw_fixtures = _load_raw_fixture_index(data_mode)
    milestones = _available_milestones(config, raw_fixtures)
    match_model = create_match_model(model_type, data_mode)

    snapshots: list[ProbabilitySnapshotResponse] = []
    previous_played: frozenset[str] = frozenset()

    for milestone in milestones:
        sliced = _tournament_at_milestone(config, raw_fixtures, milestone)
        played_ids = _played_match_ids(sliced)
        if milestone.milestone_id != "before_group_md1" and played_ids == previous_played:
            continue
        previous_played = played_ids

        summary = run_simulations(sliced, match_model, n_simulations, seed)
        snapshots.append(
            ProbabilitySnapshotResponse(
                label=milestone.label,
                milestone_id=milestone.milestone_id,
                matchday=milestone.matchday,
                champion_probabilities={
                    team_id: summary.stage_probabilities[team_id]["champion"]
                    for team_id in summary.stage_probabilities
                },
            )
        )

    return ProbabilityHistoryResponse(snapshots=snapshots)


def _available_milestones(
    config: TournamentConfig,
    raw_fixtures: dict[str, dict[str, Any]],
) -> list[_Milestone]:
    milestones = [
        _Milestone(milestone_id, label, max_group_matchday)
        for milestone_id, label, max_group_matchday in GROUP_MILESTONES
    ]

    knockout_stages = _knockout_stages_in_config(config)
    if not knockout_stages:
        return milestones

    for stage in knockout_stages:
        stage_key = stage.lower().replace(" ", "_").replace("-", "_")
        milestone_id = f"{KNOCKOUT_MILESTONE_PREFIX}{stage_key}"
        milestones.append(
            _Milestone(
                milestone_id=milestone_id,
                label=f"After {stage}",
                max_group_matchday=3,
                knockout_through=stage,
            )
        )
    return milestones


def _knockout_stages_in_config(config: TournamentConfig) -> list[str]:
    present = {match.stage for match in config.matches if match.stage != "group"}
    return [stage for stage in ROUND_NAMES if stage in present]


def _tournament_at_milestone(
    config: TournamentConfig,
    raw_fixtures: dict[str, dict[str, Any]],
    milestone: _Milestone,
) -> TournamentConfig:
    updated_matches: list[Match] = []
    for match in config.matches:
        if _match_in_milestone_scope(match, raw_fixtures, milestone):
            if match.result is not None and match.result.played:
                updated_matches.append(match)
                continue
        updated_matches.append(match.model_copy(update={"result": None, "winner_team_id": None}))

    return TournamentConfig(
        teams=config.teams,
        groups=config.groups,
        matches=updated_matches,
    )


def _match_in_milestone_scope(
    match: Match,
    raw_fixtures: dict[str, dict[str, Any]],
    milestone: _Milestone,
) -> bool:
    if match.stage == "group":
        if milestone.max_group_matchday <= 0:
            return False
        matchday = _match_group_matchday(match.id, raw_fixtures)
        return matchday is not None and matchday <= milestone.max_group_matchday

    if milestone.knockout_through is None:
        return False

    if match.stage not in ROUND_NAMES:
        return False

    return _knockout_index(match.stage) <= _knockout_index(milestone.knockout_through)


def _knockout_index(stage: str) -> int:
    return ROUND_NAMES.index(stage)


def _played_match_ids(config: TournamentConfig) -> frozenset[str]:
    return frozenset(
        match.id
        for match in config.matches
        if match.result is not None and match.result.played
    )


def _match_group_matchday(match_id: str, raw_fixtures: dict[str, dict[str, Any]]) -> int | None:
    kickoff_date = _kickoff_date(match_id, raw_fixtures)
    if kickoff_date is None:
        return None
    return group_matchday_for_date(kickoff_date)


def _kickoff_date(match_id: str, raw_fixtures: dict[str, dict[str, Any]]) -> date | None:
    raw = raw_fixtures.get(match_id, {}).get("kickoff_utc")
    if raw is None:
        kickoff = raw_fixtures.get(match_id, {}).get("kickoff")
        if isinstance(kickoff, str) and kickoff:
            try:
                return date.fromisoformat(kickoff[:10])
            except ValueError:
                return None
        return None
    try:
        dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return dt.date()
    except (ValueError, AttributeError):
        return None


def _load_raw_fixture_index(data_mode: str) -> dict[str, dict[str, Any]]:
    path = (
        get_processed_data_dir() / "fixtures.json"
        if data_mode == "processed"
        else SAMPLE_DATA_DIR / "sample_fixtures.json"
    )
    if not path.exists():
        return {}
    data: list[dict[str, Any]] = json.loads(Path(path).read_text(encoding="utf-8"))
    return {item["id"]: item for item in data}

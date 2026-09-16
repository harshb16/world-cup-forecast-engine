"""Materialize real knockout fixtures from completed group-stage results."""

from __future__ import annotations

from datetime import date

from app.models.domain import Match, TournamentConfig
from app.services.world_cup_schedule import knockout_round_for_date
from app.simulation.group_table import calculate_group_table
from app.simulation.knockout import (
    ADVANCEMENT_PAIRINGS,
    ROUND_NAMES,
    WorldCup2026BracketBuilder,
)
from app.simulation.third_place import get_best_third_place_qualifiers

KNOCKOUT_STAGES = frozenset(ROUND_NAMES) | {"Third-place match"}
ROUND_OF_32_MATCH_COUNT = 16
ROUND_OF_32_ID_PREFIX = "R32-"
ROUND_ID_PREFIX_BY_STAGE = {
    "Round of 32": "R32-",
    "Round of 16": "R16-",
    "Quarter-finals": "QF-",
    "Semi-finals": "SF-",
    "Final": "F-",
    "Third-place match": "TP-",
}
PREVIOUS_KNOCKOUT_STAGE = {
    "Round of 16": "Round of 32",
    "Quarter-finals": "Round of 16",
    "Semi-finals": "Quarter-finals",
    "Final": "Semi-finals",
    "Third-place match": "Semi-finals",
}


def is_group_stage_complete(config: TournamentConfig) -> bool:
    """Return whether every group-stage fixture has a played result."""
    group_matches = [match for match in config.matches if match.stage == "group"]
    if len(group_matches) != 72:
        return False
    return all(
        match.result is not None and match.result.played for match in group_matches
    )


def has_knockout_fixtures(config: TournamentConfig) -> bool:
    """Return whether any knockout-stage fixtures are already present."""
    return any(match.stage in KNOCKOUT_STAGES for match in config.matches)


def compute_real_qualified_team_ids(config: TournamentConfig) -> list[str]:
    """Derive the 32 qualifiers from played group-stage results only."""
    teams_by_id = {team.id: team for team in config.teams}
    played_group_matches = [
        match
        for match in config.matches
        if match.stage == "group"
        and match.result is not None
        and match.result.played
    ]
    group_tables = {
        group.id: calculate_group_table(group, teams_by_id, played_group_matches)
        for group in sorted(config.groups, key=lambda item: item.id)
    }
    top_two_qualifiers = [
        row.team_id
        for group_id in sorted(group_tables)
        for row in group_tables[group_id][:2]
    ]
    third_place_qualifiers = [
        row.team_id
        for row in get_best_third_place_qualifiers(group_tables, count=8)
    ]
    return top_two_qualifiers + third_place_qualifiers


def build_round_of_32_matches(config: TournamentConfig) -> list[Match]:
    """Build Round-of-32 match records from real group-stage qualifiers."""
    teams_by_id = {team.id: team for team in config.teams}
    qualified_team_ids = compute_real_qualified_team_ids(config)
    pairs = WorldCup2026BracketBuilder().build_round_of_32(
        qualified_team_ids,
        teams_by_id,
    )
    return [
        Match(
            id=f"{ROUND_OF_32_ID_PREFIX}{index:02d}",
            stage="Round of 32",
            team_a_id=team_a_id,
            team_b_id=team_b_id,
            result=None,
            winner_team_id=None,
        )
        for index, (team_a_id, team_b_id) in enumerate(pairs, start=1)
    ]


def materialize_round_of_32_if_ready(config: TournamentConfig) -> list[Match]:
    """Return new Round-of-32 fixtures when the group stage is complete.

    Idempotent: returns an empty list when knockout fixtures already exist or
    the group stage is not yet finished.
    """
    if not is_group_stage_complete(config):
        return []
    if _stage_fixtures_exist(config, "Round of 32"):
        return []
    return build_round_of_32_matches(config)


def is_knockout_round_complete(config: TournamentConfig, stage: str) -> bool:
    """Return whether every fixture in a knockout round has a played result."""
    round_matches = _matches_for_stage(config, stage)
    if not round_matches:
        return False
    return all(
        match.result is not None
        and match.result.played
        and match.winner_team_id is not None
        for match in round_matches
    )


def materialize_pending_knockout_rounds(config: TournamentConfig) -> list[Match]:
    """Materialize the next knockout round(s) when the previous round is complete."""
    new_matches: list[Match] = []
    r32 = materialize_round_of_32_if_ready(config)
    if r32:
        new_matches.extend(r32)
        config = config.model_copy(update={"matches": [*config.matches, *r32]})

    transitions = [
        ("Round of 32", "Round of 16"),
        ("Round of 16", "Quarter-finals"),
        ("Quarter-finals", "Semi-finals"),
        ("Semi-finals", "Final"),
    ]
    for completed_stage, next_stage in transitions:
        if not is_knockout_round_complete(config, completed_stage):
            continue
        if _stage_fixtures_exist(config, next_stage):
            continue
        round_matches = build_next_knockout_round(config, completed_stage, next_stage)
        new_matches.extend(round_matches)
        config = config.model_copy(update={"matches": [*config.matches, *round_matches]})

    if (
        is_knockout_round_complete(config, "Semi-finals")
        and not _stage_fixtures_exist(config, "Third-place match")
    ):
        third_place_matches = build_third_place_match(config)
        new_matches.extend(third_place_matches)
        config = config.model_copy(update={"matches": [*config.matches, *third_place_matches]})

    return new_matches


def build_next_knockout_round(
    config: TournamentConfig,
    completed_stage: str,
    next_stage: str,
) -> list[Match]:
    """Build knockout fixtures for the next round from real winners."""
    if next_stage == "Final":
        return build_final_match(config)
    winners = _ordered_winners(config, completed_stage)
    pairings = ADVANCEMENT_PAIRINGS[next_stage]
    prefix = ROUND_ID_PREFIX_BY_STAGE[next_stage]
    return [
        Match(
            id=f"{prefix}{index:02d}",
            stage=next_stage,
            team_a_id=winners[first_index],
            team_b_id=winners[second_index],
            result=None,
            winner_team_id=None,
        )
        for index, (first_index, second_index) in enumerate(pairings, start=1)
    ]


def build_final_match(config: TournamentConfig) -> list[Match]:
    """Build the Final from Semi-final winners."""
    winners = _ordered_winners(config, "Semi-finals")
    return [
        Match(
            id="F-01",
            stage="Final",
            team_a_id=winners[0],
            team_b_id=winners[1],
            result=None,
            winner_team_id=None,
        )
    ]


def build_third_place_match(config: TournamentConfig) -> list[Match]:
    """Build the third-place playoff from Semi-final losers."""
    semi_matches = _matches_for_stage(config, "Semi-finals")
    losers = [
        match.team_b_id if match.winner_team_id == match.team_a_id else match.team_a_id
        for match in sorted(semi_matches, key=lambda item: item.id)
    ]
    return [
        Match(
            id="TP-01",
            stage="Third-place match",
            team_a_id=losers[0],
            team_b_id=losers[1],
            result=None,
            winner_team_id=None,
        )
    ]


def winners_from_previous_round(
    fixtures: list[dict[str, object]],
    stage: str,
) -> set[str]:
    """Return team ids that won the knockout round before ``stage``."""
    previous_stage = PREVIOUS_KNOCKOUT_STAGE.get(stage)
    if previous_stage is None:
        return set()
    return {
        str(fixture["winner_team_id"])
        for fixture in fixtures
        if fixture.get("stage") == previous_stage
        and fixture.get("winner_team_id") is not None
    }


def _stage_fixtures_exist(config: TournamentConfig, stage: str) -> bool:
    return bool(_matches_for_stage(config, stage))


def _matches_for_stage(config: TournamentConfig, stage: str) -> list[Match]:
    return [match for match in config.matches if match.stage == stage]


def _ordered_winners(config: TournamentConfig, stage: str) -> list[str]:
    round_matches = sorted(_matches_for_stage(config, stage), key=lambda item: item.id)
    winners: list[str] = []
    for match in round_matches:
        if match.winner_team_id is None:
            raise ValueError(f"incomplete knockout round: {stage}")
        winners.append(match.winner_team_id)
    return winners


def knockout_stage_label(match_date: date) -> str:
    """Return a human-readable knockout round label for a calendar date."""
    round_name = knockout_round_for_date(match_date)
    return round_name if round_name is not None else "Knockout"

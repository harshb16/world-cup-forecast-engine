"""Materialize real knockout fixtures from completed group-stage results."""

from __future__ import annotations

from datetime import date

from app.models.domain import Match, TournamentConfig
from app.services.world_cup_schedule import knockout_round_for_date
from app.simulation.group_table import calculate_group_table
from app.simulation.knockout import ROUND_NAMES, WorldCup2026BracketBuilder
from app.simulation.third_place import get_best_third_place_qualifiers

KNOCKOUT_STAGES = frozenset(ROUND_NAMES) | {"Third-place match"}
ROUND_OF_32_MATCH_COUNT = 16
ROUND_OF_32_ID_PREFIX = "R32-"


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
    if has_knockout_fixtures(config):
        return []
    return build_round_of_32_matches(config)


def knockout_stage_label(match_date: date) -> str:
    """Return a human-readable knockout round label for a calendar date."""
    round_name = knockout_round_for_date(match_date)
    return round_name if round_name is not None else "Knockout"

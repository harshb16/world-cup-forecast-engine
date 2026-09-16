"""FIFA World Cup 2026 group table calculation.

Equal-points order: head-to-head points, goal difference, and goals scored;
reapply those criteria to any still-tied subset; then overall goal difference,
overall goals scored, conduct score, FIFA ranking, and deterministic team ID.
"""

from collections.abc import Callable, Iterable
from math import inf
from typing import Any, TypeVar

from app.models.domain import Group, GroupStandingRow, Match, Team

T = TypeVar("T")


def calculate_group_table(
    group: Group,
    teams_by_id: dict[str, Team],
    matches: list[Match],
) -> list[GroupStandingRow]:
    """Calculate standings using FIFA World Cup 2026 group tiebreakers."""
    rows = {
        team_id: {
            "team_id": team_id,
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "conduct_score": 0,
        }
        for team_id in group.team_ids
    }

    for team_id in group.team_ids:
        if team_id not in teams_by_id:
            raise ValueError(f"unknown team id in group: {team_id}")

    played_matches = [
        match
        for match in matches
        if match.group_id == group.id
        and match.result is not None
        and match.result.played
    ]

    for match in matches:
        if match.group_id != group.id:
            continue
        if match.team_a_id not in rows or match.team_b_id not in rows:
            raise ValueError("group match contains teams outside the group")

    for match in played_matches:
        _apply_match(rows, match)

    standing_rows = [
        GroupStandingRow(
            **row,
            goal_difference=row["goals_for"] - row["goals_against"],
            points=(row["wins"] * 3) + row["draws"],
            fifa_ranking=teams_by_id[row["team_id"]].fifa_ranking,
        )
        for row in rows.values()
    ]
    rows_by_id = {row.team_id: row for row in standing_rows}

    ranked: list[GroupStandingRow] = []
    for points_group in _partition(
        standing_rows,
        key=lambda row: row.points,
        reverse=True,
    ):
        if len(points_group) == 1:
            ranked.extend(points_group)
        else:
            ranked.extend(
                _rank_equal_points(
                    [row.team_id for row in points_group],
                    rows_by_id,
                    played_matches,
                )
            )
    return ranked


def _apply_match(rows: dict[str, dict[str, int | str]], match: Match) -> None:
    if match.result is None:
        return

    team_a = rows[match.team_a_id]
    team_b = rows[match.team_b_id]
    team_a_goals = match.result.team_a_goals
    team_b_goals = match.result.team_b_goals

    team_a["played"] += 1
    team_b["played"] += 1
    team_a["goals_for"] += team_a_goals
    team_a["goals_against"] += team_b_goals
    team_b["goals_for"] += team_b_goals
    team_b["goals_against"] += team_a_goals
    team_a["conduct_score"] += match.result.team_a_conduct_score
    team_b["conduct_score"] += match.result.team_b_conduct_score

    if team_a_goals > team_b_goals:
        team_a["wins"] += 1
        team_b["losses"] += 1
    elif team_a_goals < team_b_goals:
        team_b["wins"] += 1
        team_a["losses"] += 1
    else:
        team_a["draws"] += 1
        team_b["draws"] += 1


def _rank_equal_points(
    team_ids: list[str],
    overall_rows: dict[str, GroupStandingRow],
    played_matches: list[Match],
) -> list[GroupStandingRow]:
    """Apply head-to-head criteria, recursively reapplying them to tied subsets."""
    mini_rows = _mini_table(team_ids, played_matches)
    head_to_head_groups = _partition(
        team_ids,
        key=lambda team_id: (
            mini_rows[team_id].points,
            mini_rows[team_id].goal_difference,
            mini_rows[team_id].goals_for,
        ),
        reverse=True,
    )

    if len(head_to_head_groups) == 1:
        return _rank_by_overall_fallback(team_ids, overall_rows)

    ranked: list[GroupStandingRow] = []
    for tied_subset in head_to_head_groups:
        if len(tied_subset) == 1:
            ranked.append(overall_rows[tied_subset[0]])
        else:
            ranked.extend(
                _rank_equal_points(tied_subset, overall_rows, played_matches)
            )
    return ranked


def _mini_table(
    team_ids: list[str],
    played_matches: list[Match],
) -> dict[str, GroupStandingRow]:
    tied_ids = set(team_ids)
    raw_rows: dict[str, dict[str, int | str]] = {
        team_id: {
            "team_id": team_id,
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "conduct_score": 0,
        }
        for team_id in team_ids
    }
    for match in played_matches:
        if match.team_a_id in tied_ids and match.team_b_id in tied_ids:
            _apply_match(raw_rows, match)

    return {
        team_id: GroupStandingRow(
            **row,
            goal_difference=row["goals_for"] - row["goals_against"],
            points=(row["wins"] * 3) + row["draws"],
        )
        for team_id, row in raw_rows.items()
    }


def _rank_by_overall_fallback(
    team_ids: list[str],
    rows_by_id: dict[str, GroupStandingRow],
) -> list[GroupStandingRow]:
    return sorted(
        (rows_by_id[team_id] for team_id in team_ids),
        key=lambda row: (
            -row.goal_difference,
            -row.goals_for,
            -row.conduct_score,
            row.fifa_ranking if row.fifa_ranking is not None else inf,
            row.team_id,
        ),
    )


def _partition(
    values: Iterable[T],
    *,
    key: Callable[[T], Any],
    reverse: bool,
) -> list[list[T]]:
    ordered = sorted(values, key=key, reverse=reverse)
    groups: list[list[T]] = []
    for value in ordered:
        if not groups or key(groups[-1][0]) != key(value):
            groups.append([value])
        else:
            groups[-1].append(value)
    return groups

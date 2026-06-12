"""Group table calculation module."""

from app.models.domain import Group, GroupStandingRow, Match, Team


def calculate_group_table(
    group: Group,
    teams_by_id: dict[str, Team],
    matches: list[Match],
) -> list[GroupStandingRow]:
    """Calculate and rank standings for a single group."""
    rows = {
        team_id: {
            "team_id": team_id,
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
        }
        for team_id in group.team_ids
    }

    for team_id in group.team_ids:
        if team_id not in teams_by_id:
            raise ValueError(f"unknown team id in group: {team_id}")

    for match in matches:
        if match.group_id != group.id or match.result is None or not match.result.played:
            continue
        if match.team_a_id not in rows or match.team_b_id not in rows:
            continue

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

        if team_a_goals > team_b_goals:
            team_a["wins"] += 1
            team_b["losses"] += 1
        elif team_a_goals < team_b_goals:
            team_b["wins"] += 1
            team_a["losses"] += 1
        else:
            team_a["draws"] += 1
            team_b["draws"] += 1

    standing_rows = [
        GroupStandingRow(
            **row,
            goal_difference=row["goals_for"] - row["goals_against"],
            points=(row["wins"] * 3) + row["draws"],
        )
        for row in rows.values()
    ]

    return sorted(
        standing_rows,
        key=lambda row: (-row.points, -row.goal_difference, -row.goals_for, row.team_id),
    )

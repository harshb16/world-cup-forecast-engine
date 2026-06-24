"""Third-place ranking module."""

from math import inf

from app.models.domain import GroupStandingRow


def get_third_place_rows(
    group_tables: dict[str, list[GroupStandingRow]],
) -> list[GroupStandingRow]:
    """Extract the third-ranked row from each group table."""
    third_place_rows: list[GroupStandingRow] = []

    for group_id in sorted(group_tables):
        table = group_tables[group_id]
        if len(table) < 3:
            raise ValueError(f"group {group_id} does not have a third-place row")
        third_place_rows.append(table[2])

    return third_place_rows


def rank_third_place_teams(
    group_tables: dict[str, list[GroupStandingRow]],
) -> list[GroupStandingRow]:
    """Rank third-place teams using tournament tiebreakers."""
    return sorted(
        get_third_place_rows(group_tables),
        key=lambda row: (
            -row.points,
            -row.goal_difference,
            -row.goals_for,
            -row.conduct_score,
            row.fifa_ranking if row.fifa_ranking is not None else inf,
            row.team_id,
        ),
    )


def get_best_third_place_qualifiers(
    group_tables: dict[str, list[GroupStandingRow]],
    count: int = 8,
) -> list[GroupStandingRow]:
    """Return the best third-place qualifiers."""
    if count < 0:
        raise ValueError("qualifier count must be non-negative")

    return rank_third_place_teams(group_tables)[:count]

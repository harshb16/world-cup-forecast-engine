"""Official FIFA World Cup 2026 tournament schedule helpers."""

from datetime import date

GROUP_MATCHDAY_WINDOWS = (
    (date(2026, 6, 11), date(2026, 6, 17), 1),
    (date(2026, 6, 18), date(2026, 6, 23), 2),
    (date(2026, 6, 24), date(2026, 6, 27), 3),
)

KNOCKOUT_ROUND_WINDOWS: tuple[tuple[date, date, str], ...] = (
    (date(2026, 6, 28), date(2026, 7, 3), "Round of 32"),
    (date(2026, 7, 4), date(2026, 7, 7), "Round of 16"),
    (date(2026, 7, 9), date(2026, 7, 11), "Quarter-finals"),
    (date(2026, 7, 14), date(2026, 7, 15), "Semi-finals"),
    (date(2026, 7, 18), date(2026, 7, 18), "Third-place match"),
    (date(2026, 7, 19), date(2026, 7, 19), "Final"),
)


def group_matchday_for_date(match_date: date) -> int | None:
    """Return FIFA's official group-stage matchday for a calendar date."""
    for start_date, end_date, matchday in GROUP_MATCHDAY_WINDOWS:
        if start_date <= match_date <= end_date:
            return matchday
    return None


def group_matchday_label(match_date: date) -> str:
    """Return the official group-stage label for a calendar date."""
    matchday = group_matchday_for_date(match_date)
    return f"Matchday {matchday}" if matchday is not None else "Matchday"


def knockout_round_for_date(match_date: date) -> str | None:
    """Return the FIFA World Cup 2026 knockout round for a calendar date."""
    for start_date, end_date, round_name in KNOCKOUT_ROUND_WINDOWS:
        if start_date <= match_date <= end_date:
            return round_name
    return None


def tournament_stage_label(match_date: date) -> str:
    """Return group matchday or knockout round label for a calendar date."""
    group_matchday = group_matchday_for_date(match_date)
    if group_matchday is not None:
        return f"Matchday {group_matchday}"
    knockout_round = knockout_round_for_date(match_date)
    if knockout_round is not None:
        return knockout_round
    return "Matchday"

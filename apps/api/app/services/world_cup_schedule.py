"""Official FIFA World Cup 2026 tournament schedule helpers."""

from datetime import date

GROUP_MATCHDAY_WINDOWS = (
    (date(2026, 6, 11), date(2026, 6, 17), 1),
    (date(2026, 6, 18), date(2026, 6, 23), 2),
    (date(2026, 6, 24), date(2026, 6, 27), 3),
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

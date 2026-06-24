"""Tests for official FIFA World Cup 2026 matchday windows."""

from datetime import date

import pytest

from app.services.world_cup_schedule import (
    group_matchday_for_date,
    group_matchday_label,
)


@pytest.mark.parametrize(
    ("match_date", "expected"),
    [
        (date(2026, 6, 11), 1),
        (date(2026, 6, 17), 1),
        (date(2026, 6, 18), 2),
        (date(2026, 6, 23), 2),
        (date(2026, 6, 24), 3),
        (date(2026, 6, 27), 3),
    ],
)
def test_group_matchday_for_official_date_windows(
    match_date: date,
    expected: int,
) -> None:
    assert group_matchday_for_date(match_date) == expected


def test_dates_outside_group_stage_have_no_matchday() -> None:
    assert group_matchday_for_date(date(2026, 6, 10)) is None
    assert group_matchday_for_date(date(2026, 6, 28)) is None
    assert group_matchday_label(date(2026, 6, 28)) == "Matchday"

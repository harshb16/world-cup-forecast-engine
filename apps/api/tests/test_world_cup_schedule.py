"""Tests for FIFA World Cup 2026 schedule helpers."""

from datetime import date

from app.services.world_cup_schedule import (
    group_matchday_for_date,
    knockout_round_for_date,
    tournament_stage_label,
)


def test_group_matchday_for_date() -> None:
    assert group_matchday_for_date(date(2026, 6, 11)) == 1
    assert group_matchday_for_date(date(2026, 6, 20)) == 2
    assert group_matchday_for_date(date(2026, 6, 27)) == 3
    assert group_matchday_for_date(date(2026, 7, 1)) is None


def test_knockout_round_for_date() -> None:
    assert knockout_round_for_date(date(2026, 7, 3)) == "Round of 32"
    assert knockout_round_for_date(date(2026, 7, 7)) == "Round of 16"


def test_tournament_stage_label() -> None:
    assert tournament_stage_label(date(2026, 6, 18)) == "Matchday 2"
    assert tournament_stage_label(date(2026, 7, 19)) == "Final"

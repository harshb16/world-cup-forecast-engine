"""Normalize provider match statuses into tournament match states."""

from __future__ import annotations

from typing import Any

from app.models.schemas import MatchStatus

FOOTBALL_DATA_FINISHED = {"FINISHED"}
FOOTBALL_DATA_IN_PLAY = {"IN_PLAY", "PAUSED", "LIVE", "HALF_TIME", "EXTRA_TIME"}
FIFA_FINISHED = {0, 3}
FIFA_IN_PLAY = {1, 2}


def normalize_match_status(value: str | MatchStatus) -> MatchStatus:
    """Return a supported match status or raise."""
    if value not in {"scheduled", "in_play", "finished"}:
        raise ValueError(f"Unsupported match status: {value}")
    return value  # type: ignore[return-value]


def football_data_status(raw_status: str | None) -> MatchStatus:
    """Map football-data.org status codes."""
    status = (raw_status or "").upper()
    if status in FOOTBALL_DATA_FINISHED:
        return "finished"
    if status in FOOTBALL_DATA_IN_PLAY:
        return "in_play"
    return "scheduled"


def fifa_status(raw_status: Any) -> MatchStatus:
    """Map FIFA calendar MatchStatus integers."""
    if raw_status in FIFA_FINISHED:
        return "finished"
    if raw_status in FIFA_IN_PLAY:
        return "in_play"
    return "scheduled"

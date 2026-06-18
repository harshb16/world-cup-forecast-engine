"""Matchday service — today's fixtures with probabilities and live group tables."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.models.domain import Group, Match, Team
from app.models.schemas import (
    MatchdayFixtureResponse,
    MatchdayGroupResponse,
    MatchdayGroupStanding,
    MatchdayResponse,
    ModelType,
)
from app.services.data_loader import PROCESSED_DATA_DIR, load_tournament
from app.services.simulation_service import create_match_model
from app.simulation.group_table import calculate_group_table

_MAX_SCORELINE = 6


def calculate_matchday(
    data_mode: str,
    model_type: ModelType = "oracle_v2",
) -> MatchdayResponse:
    """Return today's fixtures with model probabilities and real group standings."""
    config = load_tournament(data_mode)
    teams_by_id: dict[str, Team] = {t.id: t for t in config.teams}

    match_model = create_match_model(model_type, data_mode)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    group_matches = [m for m in config.matches if m.stage == "group"]

    today_fixtures = [
        m
        for m in group_matches
        if m.result is None or not m.result.played
        if _kickoff_date(m) == today_str
    ]

    # Fallback: if no matches today use all unplayed matches
    if not today_fixtures:
        today_fixtures = [
            m for m in group_matches if m.result is None or not m.result.played
        ]

    fixture_responses = [
        _build_fixture_response(match, teams_by_id, match_model)
        for match in today_fixtures
    ]

    # Determine which unplayed matches are "still matter" for group qualification
    _annotate_matters(fixture_responses, config.groups, group_matches, teams_by_id)

    # Build real group standings from completed results
    group_responses = [
        _build_group_response(group, teams_by_id, group_matches)
        for group in sorted(config.groups, key=lambda g: g.id)
    ]

    matchday_label = _matchday_label(data_mode)

    return MatchdayResponse(
        date=today_str,
        matchday_label=matchday_label,
        model_type=model_type,
        fixtures=fixture_responses,
        groups=group_responses,
    )


def _kickoff_date(match: Match) -> str | None:
    """Return the UTC date string for a match's kickoff_utc field."""
    raw = _raw_fixture_field(match.id, "kickoff_utc")
    if raw is None:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def _raw_fixture_field(match_id: str, field: str) -> Any:
    """Read a raw field from fixtures.json (supports extra fields not in domain model)."""
    cache = _fixture_raw_cache()
    entry = cache.get(match_id)
    if entry is None:
        return None
    return entry.get(field)


_fixture_cache: dict[str, dict[str, Any]] | None = None


def _fixture_raw_cache() -> dict[str, dict[str, Any]]:
    global _fixture_cache
    if _fixture_cache is None:
        path = PROCESSED_DATA_DIR / "fixtures.json"
        if path.exists():
            data: list[dict[str, Any]] = json.loads(path.read_text())
            _fixture_cache = {item["id"]: item for item in data}
        else:
            _fixture_cache = {}
    return _fixture_cache


def _build_fixture_response(
    match: Match,
    teams_by_id: dict[str, Team],
    match_model: Any,
) -> MatchdayFixtureResponse:
    team_a = teams_by_id[match.team_a_id]
    team_b = teams_by_id[match.team_b_id]

    raw = _fixture_raw_cache().get(match.id, {})
    kickoff_utc: str | None = raw.get("kickoff_utc")
    status: str = raw.get("status", "scheduled")

    probs = match_model.predict_probabilities(team_a, team_b)

    projected_a, projected_b = _projected_scoreline(match_model, team_a, team_b)

    team_a_goals: int | None = None
    team_b_goals: int | None = None
    if match.result is not None and match.result.played:
        team_a_goals = match.result.team_a_goals
        team_b_goals = match.result.team_b_goals

    return MatchdayFixtureResponse(
        match_id=match.id,
        group_id=match.group_id,
        kickoff_utc=kickoff_utc,
        status=status,
        stage=match.stage,
        team_a_id=match.team_a_id,
        team_a_name=team_a.name,
        team_b_id=match.team_b_id,
        team_b_name=team_b.name,
        team_a_win_probability=round(probs["team_a_win"], 4),
        draw_probability=round(probs["draw"], 4),
        team_b_win_probability=round(probs["team_b_win"], 4),
        projected_team_a_goals=projected_a,
        projected_team_b_goals=projected_b,
        team_a_goals=team_a_goals,
        team_b_goals=team_b_goals,
        what_still_matters=False,  # annotated in a second pass
    )


def _projected_scoreline(
    match_model: Any,
    team_a: Team,
    team_b: Team,
) -> tuple[float, float]:
    """Return expected goals as a projected scoreline."""
    expected_goals_fn = getattr(match_model, "expected_goals", None)
    if callable(expected_goals_fn):
        a, b = expected_goals_fn(team_a, team_b)
        return round(float(a), 1), round(float(b), 1)
    # Fall back to prob-weighted outcome
    probs = match_model.predict_probabilities(team_a, team_b)
    if probs["team_a_win"] > probs["team_b_win"] + 0.05:
        return 1.5, 0.8
    if probs["team_b_win"] > probs["team_a_win"] + 0.05:
        return 0.8, 1.5
    return 1.1, 1.1


def _annotate_matters(
    fixtures: list[MatchdayFixtureResponse],
    groups: list[Group],
    all_group_matches: list[Match],
    teams_by_id: dict[str, Team],
) -> None:
    """Set what_still_matters=True when a result could change group qualification."""
    groups_by_id = {g.id: g for g in groups}

    for fixture in fixtures:
        if fixture.status == "finished":
            continue
        if fixture.group_id is None:
            continue
        group = groups_by_id.get(fixture.group_id)
        if group is None:
            continue

        # Check if any two team's point totals are within 3 of each other (still live)
        current_table = calculate_group_table(group, teams_by_id, all_group_matches)
        points = [row.points for row in current_table]
        if len(points) >= 2:
            spread = points[0] - points[-1]
            # if spread < 7 the group is still live (3 pts available per remaining game)
            fixture.what_still_matters = spread < 7


def _build_group_response(
    group: Group,
    teams_by_id: dict[str, Team],
    all_group_matches: list[Match],
) -> MatchdayGroupResponse:
    table = calculate_group_table(group, teams_by_id, all_group_matches)

    standings = [
        MatchdayGroupStanding(
            position=idx + 1,
            team_id=row.team_id,
            team_name=teams_by_id[row.team_id].name,
            played=row.played,
            wins=row.wins,
            draws=row.draws,
            losses=row.losses,
            goals_for=row.goals_for,
            goals_against=row.goals_against,
            goal_difference=row.goal_difference,
            points=row.points,
        )
        for idx, row in enumerate(table)
    ]

    total_matches = len(group.team_ids) * (len(group.team_ids) - 1) // 2
    played_in_group = sum(
        1
        for m in all_group_matches
        if m.group_id == group.id and m.result is not None and m.result.played
    )
    is_complete = played_in_group >= total_matches

    return MatchdayGroupResponse(
        group_id=group.id,
        group_name=group.name,
        standings=standings,
        is_complete=is_complete,
    )


def _matchday_label(data_mode: str) -> str:
    """Derive a human-readable matchday label from completed match count."""
    try:
        path = PROCESSED_DATA_DIR / "fixtures.json"
        if not path.exists():
            return "Matchday"
        data: list[dict[str, Any]] = json.loads(path.read_text())
        played = sum(1 for f in data if f.get("status") == "finished")
        if played == 0:
            return "Matchday 1"
        matchday = (played // 24) + 1
        return f"Matchday {matchday}"
    except Exception:
        return "Matchday"

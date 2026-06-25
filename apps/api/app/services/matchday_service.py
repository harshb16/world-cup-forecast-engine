"""Matchday service — today's fixtures with probabilities and live group tables."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from app.core.config import DEFAULT_MODEL_TYPE
from app.models.domain import Group, Match, Team
from app.models.schemas import (
    MatchdayFixtureResponse,
    MatchdayGroupResponse,
    MatchdayGroupStanding,
    MatchdayResponse,
    ModelType,
)
from app.services.data_loader import (
    get_processed_data_dir,
    SAMPLE_DATA_DIR,
    load_tournament,
)
from app.services.simulation_service import create_match_model
from app.services.world_cup_schedule import group_matchday_label
from app.simulation.group_table import calculate_group_table


def calculate_matchday(
    data_mode: str,
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    as_of_date: date | None = None,
) -> MatchdayResponse:
    """Return today's fixtures with model probabilities and real group standings."""
    config = load_tournament(data_mode)
    teams_by_id: dict[str, Team] = {t.id: t for t in config.teams}

    match_model = create_match_model(model_type, data_mode)
    raw_fixtures = _load_raw_fixture_index(data_mode)

    requested_date = as_of_date or datetime.now(timezone.utc).date()
    group_matches = [m for m in config.matches if m.stage == "group"]
    unplayed_matches = [
        match
        for match in group_matches
        if match.result is None or not match.result.played
    ]
    display_candidates = group_matches if as_of_date is not None else unplayed_matches

    today_fixtures = [
        m
        for m in display_candidates
        if _kickoff_date(m, raw_fixtures) == requested_date
    ]

    display_date = requested_date
    # If today is idle, show the next scheduled group-stage date.
    if not today_fixtures:
        future_dates = [
            kickoff_date
            for match in display_candidates
            if (kickoff_date := _kickoff_date(match, raw_fixtures)) is not None
            and kickoff_date >= requested_date
        ]
        if future_dates:
            display_date = min(future_dates)
            today_fixtures = [
                match
                for match in display_candidates
                if _kickoff_date(match, raw_fixtures) == display_date
            ]
        else:
            today_fixtures = display_candidates

    fixture_responses = [
        _build_fixture_response(match, teams_by_id, match_model, raw_fixtures)
        for match in today_fixtures
    ]

    # Determine which unplayed matches are "still matter" for group qualification
    _annotate_matters(fixture_responses, config.groups, group_matches, teams_by_id)

    # Build real group standings from completed results
    group_responses = [
        _build_group_response(group, teams_by_id, group_matches)
        for group in sorted(config.groups, key=lambda g: g.id)
    ]

    return MatchdayResponse(
        date=display_date.isoformat(),
        matchday_label=group_matchday_label(display_date),
        model_type=model_type,
        fixtures=fixture_responses,
        groups=group_responses,
    )


def _kickoff_date(
    match: Match,
    raw_fixtures: dict[str, dict[str, Any]],
) -> date | None:
    """Return the UTC date for a match's kickoff_utc field."""
    raw = raw_fixtures.get(match.id, {}).get("kickoff_utc")
    if raw is None:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.date()
    except (ValueError, AttributeError):
        return None


def _load_raw_fixture_index(data_mode: str) -> dict[str, dict[str, Any]]:
    path = (
        get_processed_data_dir() / "fixtures.json"
        if data_mode == "processed"
        else SAMPLE_DATA_DIR / "sample_fixtures.json"
    )
    if not path.exists():
        return {}
    data: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return {item["id"]: item for item in data}


def _build_fixture_response(
    match: Match,
    teams_by_id: dict[str, Team],
    match_model: Any,
    raw_fixtures: dict[str, dict[str, Any]],
) -> MatchdayFixtureResponse:
    team_a = teams_by_id[match.team_a_id]
    team_b = teams_by_id[match.team_b_id]

    raw = raw_fixtures.get(match.id, {})
    kickoff_utc: str | None = raw.get("kickoff_utc")
    status: str = raw.get(
        "status",
        "finished" if match.result is not None and match.result.played else "scheduled",
    )

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

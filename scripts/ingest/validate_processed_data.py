"""Validate processed World Cup 2026 data files."""

from __future__ import annotations

from datetime import date, datetime

from common import PROCESSED_DIR, read_json

ALLOWED_FIXTURE_STATUSES = {"scheduled", "finished"}


def _parse_kickoff_date(fixture: dict, errors: list[str]) -> date | None:
    fixture_id = fixture.get("id", "<missing id>")
    kickoff = fixture.get("kickoff")
    if not isinstance(kickoff, str):
        errors.append(f"{fixture_id} must have an ISO kickoff date")
        return None
    try:
        return date.fromisoformat(kickoff)
    except ValueError:
        errors.append(f"{fixture_id} has invalid kickoff date")
        return None


def _parse_kickoff_utc(fixture: dict, errors: list[str]) -> datetime | None:
    fixture_id = fixture.get("id", "<missing id>")
    kickoff_utc = fixture.get("kickoff_utc")
    if not isinstance(kickoff_utc, str):
        errors.append(f"{fixture_id} must have an ISO kickoff_utc datetime")
        return None
    try:
        parsed = datetime.fromisoformat(kickoff_utc.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{fixture_id} has invalid kickoff_utc datetime")
        return None
    if parsed.utcoffset() is None:
        errors.append(f"{fixture_id} kickoff_utc must include a timezone")
        return None
    return parsed


def _expected_winner_id(fixture: dict) -> str | None:
    result = fixture.get("result")
    if not isinstance(result, dict):
        return None
    if result.get("decided_by_penalties"):
        penalty_a = result.get("penalty_team_a_goals")
        penalty_b = result.get("penalty_team_b_goals")
        if type(penalty_a) is int and type(penalty_b) is int:
            if penalty_a > penalty_b:
                return fixture.get("team_a_id")
            if penalty_b > penalty_a:
                return fixture.get("team_b_id")
    team_a_goals = result.get("team_a_goals")
    team_b_goals = result.get("team_b_goals")
    if type(team_a_goals) is not int or type(team_b_goals) is not int:
        return None
    if team_a_goals > team_b_goals:
        return fixture.get("team_a_id")
    if team_b_goals > team_a_goals:
        return fixture.get("team_b_id")
    return None


def _validate_fixture_record(
    fixture: dict,
    *,
    team_ids: set[str],
    teams_by_id: dict[str, dict],
    group_by_id: dict[str, dict],
    errors: list[str],
    require_group_fields: bool,
) -> None:
    fixture_id = fixture.get("id", "<missing id>")
    if require_group_fields:
        group_id = fixture.get("group_id")
        if group_id not in group_by_id:
            errors.append(f"{fixture_id} has invalid group_id")
            return
        for side in ["team_a_id", "team_b_id"]:
            team_id = fixture.get(side)
            if team_id not in team_ids:
                errors.append(f"{fixture_id} references unknown team {team_id}")
            elif teams_by_id[team_id]["group_id"] != group_id:
                errors.append(f"{fixture_id} team {team_id} is not in {group_id}")
        kickoff_date = _parse_kickoff_date(fixture, errors)
        kickoff_utc = _parse_kickoff_utc(fixture, errors)
        if (
            kickoff_date is not None
            and kickoff_utc is not None
            and abs((kickoff_date - kickoff_utc.date()).days) > 1
        ):
            errors.append(f"{fixture_id} kickoff date contradicts kickoff_utc")
    else:
        for side in ["team_a_id", "team_b_id"]:
            team_id = fixture.get(side)
            if team_id not in team_ids:
                errors.append(f"{fixture_id} references unknown team {team_id}")

    result = fixture.get("result")
    status = fixture.get("status")
    winner_team_id = fixture.get("winner_team_id")
    if status not in ALLOWED_FIXTURE_STATUSES:
        errors.append(f"{fixture_id} has invalid status {status}")
        return
    if status == "finished":
        if not result:
            errors.append(f"{fixture_id} is finished but has no result")
        elif not all(
            type(result.get(key)) is int and result[key] >= 0
            for key in ["team_a_goals", "team_b_goals"]
        ):
            errors.append(f"{fixture_id} has invalid finished score")
        elif result.get("played") is not True:
            errors.append(f"{fixture_id} finished result must be marked played")
        else:
            expected_winner_id = _expected_winner_id(fixture)
            if winner_team_id != expected_winner_id:
                errors.append(f"{fixture_id} winner_team_id does not match result")
    else:
        if result is not None:
            errors.append(f"{fixture_id} is scheduled but result is not null")
        if winner_team_id is not None:
            errors.append(f"{fixture_id} is scheduled but winner_team_id is not null")


def validate_processed_data(base_dir=PROCESSED_DIR) -> list[str]:
    errors: list[str] = []
    teams = read_json(base_dir / "teams.json")
    groups = read_json(base_dir / "groups.json")
    fixtures = read_json(base_dir / "fixtures.json")
    results = read_json(base_dir / "results.json")
    ratings = read_json(base_dir / "ratings.json")
    metadata = read_json(base_dir / "metadata.json")
    model_parameters = read_json(base_dir / "model_parameters.json")
    squad_features = read_json(base_dir / "squad_features.json")

    if len(teams) != 48:
        errors.append("teams.json must contain 48 teams")
    if len(groups) != 12:
        errors.append("groups.json must contain 12 groups")

    team_ids = {team["id"] for team in teams}
    teams_by_id = {team["id"]: team for team in teams}

    group_memberships: dict[str, str] = {}
    for group in groups:
        team_ids_in_group = group.get("team_ids", [])
        if len(team_ids_in_group) != 4:
            errors.append(f"{group['id']} must contain 4 teams")
        for team_id in team_ids_in_group:
            if team_id not in team_ids:
                errors.append(f"{group['id']} contains unknown team {team_id}")
            if team_id in group_memberships:
                errors.append(f"{team_id} appears in multiple groups")
            group_memberships[team_id] = group["id"]
            if team_id in teams_by_id and teams_by_id[team_id].get("group_id") != group["id"]:
                errors.append(f"{team_id} has mismatched team.group_id")

    if set(group_memberships) != team_ids:
        errors.append("every team must belong to exactly one group")

    group_by_id = {group["id"]: group for group in groups}
    group_stage_fixtures = [fixture for fixture in fixtures if fixture.get("stage") == "group"]
    knockout_fixtures = [fixture for fixture in fixtures if fixture.get("stage") != "group"]
    if len(group_stage_fixtures) != 72:
        errors.append("fixtures.json must contain 72 group-stage fixtures")

    fixture_ids = [fixture.get("id") for fixture in fixtures]
    if len(set(fixture_ids)) != len(fixture_ids):
        errors.append("fixtures.json contains duplicate fixture ids")

    for fixture in group_stage_fixtures:
        _validate_fixture_record(
            fixture,
            team_ids=team_ids,
            teams_by_id=teams_by_id,
            group_by_id=group_by_id,
            errors=errors,
            require_group_fields=True,
        )

    for fixture in knockout_fixtures:
        _validate_fixture_record(
            fixture,
            team_ids=team_ids,
            teams_by_id=teams_by_id,
            group_by_id=group_by_id,
            errors=errors,
            require_group_fields=False,
        )

    fixtures_by_id = {fixture["id"]: fixture for fixture in fixtures}
    result_fixture_ids: set[str] = set()
    for result in results:
        match_id = result.get("match_id")
        if match_id in result_fixture_ids:
            errors.append(f"results.json contains duplicate match {match_id}")
            continue
        result_fixture_ids.add(match_id)

        fixture = fixtures_by_id.get(match_id)
        if fixture is None:
            errors.append(f"results.json references unknown match {match_id}")
            continue
        for side in ["team_a_id", "team_b_id"]:
            if result.get(side) != fixture.get(side):
                errors.append(f"{match_id} result has mismatched {side}")
        for score in ["team_a_goals", "team_b_goals"]:
            if type(result.get(score)) is not int or result[score] < 0:
                errors.append(f"{match_id} result has invalid {score}")
            fixture_result = fixture.get("result")
            fixture_score = (
                fixture_result.get(score)
                if isinstance(fixture_result, dict)
                else None
            )
            if type(result.get(score)) is int and result.get(score) != fixture_score:
                errors.append(f"{match_id} result score does not match fixtures.json")
        if result.get("status") != "finished":
            errors.append(f"{match_id} result status must be finished")

    for fixture in fixtures:
        if fixture.get("status") == "finished" and fixture["id"] not in result_fixture_ids:
            errors.append(f"{fixture['id']} finished fixture missing from results.json")

    rating_ids = {rating["team_id"] for rating in ratings}
    missing_ratings = team_ids - rating_ids
    if missing_ratings and metadata.get("rating_source") != "none":
        errors.append(f"ratings missing for teams: {', '.join(sorted(missing_ratings))}")

    required_metadata = [
        "data_mode",
        "is_real_data",
        "data_version",
        "last_updated",
        "sources",
        "rating_source",
        "ratings_are_official",
        "bracket_status",
    ]
    for key in required_metadata:
        if key not in metadata:
            errors.append(f"metadata missing {key}")

    model_parameter_ids = {
        item["team_id"]
        for item in model_parameters.get("team_ratings", [])
    }
    if model_parameter_ids != team_ids:
        errors.append("model_parameters.json must contain one rating for every team")
    if any(item.get("fallback_used") for item in model_parameters.get("team_ratings", [])):
        errors.append("model_parameters.json must not use fallback ratings")

    squad_feature_ids = {item["team_id"] for item in squad_features}
    if squad_feature_ids != team_ids:
        errors.append("squad_features.json must contain one row for every team")
    if any(item.get("squad_power", 0) <= 0 for item in squad_features):
        errors.append("squad_features.json squad_power values must be positive")

    return errors


def main() -> None:
    errors = validate_processed_data()
    if errors:
        raise SystemExit("\n".join(errors))
    print("processed data valid")


if __name__ == "__main__":
    main()

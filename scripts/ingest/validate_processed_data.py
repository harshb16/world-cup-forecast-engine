"""Validate processed World Cup 2026 data files."""

from __future__ import annotations

from common import PROCESSED_DIR, read_json


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
    if len(group_stage_fixtures) != 72:
        errors.append("fixtures.json must contain 72 group-stage fixtures")

    for fixture in group_stage_fixtures:
        group_id = fixture.get("group_id")
        if group_id not in group_by_id:
            errors.append(f"{fixture['id']} has invalid group_id")
            continue
        for side in ["team_a_id", "team_b_id"]:
            team_id = fixture.get(side)
            if team_id not in team_ids:
                errors.append(f"{fixture['id']} references unknown team {team_id}")
            elif teams_by_id[team_id]["group_id"] != group_id:
                errors.append(f"{fixture['id']} team {team_id} is not in {group_id}")
        result = fixture.get("result")
        status = fixture.get("status")
        if status == "finished":
            if not result:
                errors.append(f"{fixture['id']} is finished but has no result")
            elif not all(
                isinstance(result.get(key), int) and result[key] >= 0
                for key in ["team_a_goals", "team_b_goals"]
            ):
                errors.append(f"{fixture['id']} has invalid finished score")
        elif result is not None:
            errors.append(f"{fixture['id']} is scheduled but result is not null")

    fixtures_by_id = {fixture["id"]: fixture for fixture in group_stage_fixtures}
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
            if not isinstance(result.get(score), int) or result[score] < 0:
                errors.append(f"{match_id} result has invalid {score}")

    for fixture in group_stage_fixtures:
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

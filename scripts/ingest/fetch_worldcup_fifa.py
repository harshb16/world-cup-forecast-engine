"""Fetch World Cup 2026 fixtures/results from the FIFA public API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from common import (
    PROCESSED_DIR,
    RAW_DIR,
    FetchError,
    fetch_text,
    read_json,
    utc_now_iso,
    write_json,
)

FIFA_API_URL = (
    "https://api.fifa.com/api/v3/calendar/matches?count=500&idSeason=285023"
)
FIFA_RAW_PATH = RAW_DIR / "fifa" / "worldcup_2026_api.json"

FIFA_ABBREV_TO_TEAM_ID: dict[str, str] = {
    "MEX": "MEXICO",
    "RSA": "RSA",
    "KOR": "KOR",
    "CZE": "CZECHIA",
    "CAN": "CANADA",
    "QAT": "QATAR",
    "BIH": "BIH",
    "SUI": "SWITZERLAND",
    "BRA": "BRAZIL",
    "MAR": "MOROCCO",
    "HAI": "HAITI",
    "SCO": "SCOTLAND",
    "USA": "USA",
    "PAR": "PARAGUAY",
    "AUS": "AUSTRALIA",
    "TUR": "TURKIYE",
    "GER": "GERMANY",
    "CUW": "CURACAO",
    "CIV": "CIV",
    "ECU": "ECUADOR",
    "NED": "NETHERLANDS",
    "JPN": "JAPAN",
    "SWE": "SWEDEN",
    "TUN": "TUNISIA",
    "BEL": "BELGIUM",
    "EGY": "EGYPT",
    "IRN": "IRN",
    "NZL": "NEW_ZEALAND",
    "ESP": "SPAIN",
    "CPV": "CPV",
    "KSA": "SAUDI_ARABIA",
    "URU": "URUGUAY",
    "FRA": "FRANCE",
    "SEN": "SENEGAL",
    "IRQ": "IRAQ",
    "NOR": "NORWAY",
    "ARG": "ARGENTINA",
    "ALG": "ALGERIA",
    "AUT": "AUSTRIA",
    "JOR": "JORDAN",
    "POR": "PORTUGAL",
    "COD": "COD",
    "UZB": "UZBEKISTAN",
    "COL": "COLOMBIA",
    "ENG": "ENGLAND",
    "CRO": "CROATIA",
    "GHA": "GHANA",
    "PAN": "PANAMA",
}

RESULT_SOURCE = "FIFA API v3 calendar/matches (idSeason=285023)"


def team_id_from_fifa_side(side: dict[str, Any]) -> str | None:
    abbreviation = side.get("Abbreviation")
    if not isinstance(abbreviation, str):
        return None
    return FIFA_ABBREV_TO_TEAM_ID.get(abbreviation.upper())


def sorted_team_pair(team_a_id: str, team_b_id: str) -> tuple[str, str]:
    return tuple(sorted((team_a_id, team_b_id)))


def build_fifa_match_index(
    fifa_matches: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for match in fifa_matches:
        placeholder = match.get("PlaceHolderA")
        if not isinstance(placeholder, str) or len(placeholder) != 2:
            continue
        home = team_id_from_fifa_side(match.get("Home") or {})
        away = team_id_from_fifa_side(match.get("Away") or {})
        if home is None or away is None:
            continue
        index[sorted_team_pair(home, away)] = match
    return index


def fixture_status_from_fifa(match: dict[str, Any]) -> str:
    status = match.get("MatchStatus")
    if status in (0, 3):
        return "finished"
    return "scheduled"


def extract_fixture_result(
    fixture: dict[str, Any],
    fifa_match: dict[str, Any],
) -> dict[str, Any] | None:
    if fixture_status_from_fifa(fifa_match) != "finished":
        return None
    home_score = fifa_match.get("HomeTeamScore")
    away_score = fifa_match.get("AwayTeamScore")
    if home_score is None or away_score is None:
        return None
    home_id = team_id_from_fifa_side(fifa_match.get("Home") or {})
    away_id = team_id_from_fifa_side(fifa_match.get("Away") or {})
    if home_id is None or away_id is None:
        return None
    if fixture["team_a_id"] == home_id and fixture["team_b_id"] == away_id:
        team_a_goals, team_b_goals = int(home_score), int(away_score)
    elif fixture["team_a_id"] == away_id and fixture["team_b_id"] == home_id:
        team_a_goals, team_b_goals = int(away_score), int(home_score)
    else:
        return None
    return {
        "played": True,
        "team_a_goals": team_a_goals,
        "team_b_goals": team_b_goals,
    }


def kickoff_utc_from_fifa(match: dict[str, Any]) -> str | None:
    kickoff = match.get("KickOffTimeUtc") or match.get("Date")
    if isinstance(kickoff, str) and kickoff:
        return kickoff
    return None


def apply_fifa_updates(
    fixtures: list[dict[str, Any]],
    fifa_matches: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fifa_index = build_fifa_match_index(fifa_matches)
    updated_fixtures: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []

    for fixture in fixtures:
        updated = dict(fixture)
        if fixture.get("stage") != "group":
            updated_fixtures.append(updated)
            continue
        pair = sorted_team_pair(fixture["team_a_id"], fixture["team_b_id"])
        fifa_match = fifa_index.get(pair)
        if fifa_match is None:
            updated_fixtures.append(updated)
            continue
        kickoff = kickoff_utc_from_fifa(fifa_match)
        if kickoff is not None:
            updated["kickoff_utc"] = kickoff
        stadium = fifa_match.get("StadiumName")
        if isinstance(stadium, str) and stadium:
            updated["venue"] = stadium
        updated["status"] = fixture_status_from_fifa(fifa_match)
        result = extract_fixture_result(updated, fifa_match)
        updated["result"] = result
        updated_fixtures.append(updated)
        if result is not None:
            results.append(
                {
                    "match_id": fixture["id"],
                    "team_a_id": fixture["team_a_id"],
                    "team_b_goals": result["team_b_goals"],
                    "team_a_goals": result["team_a_goals"],
                    "status": "finished",
                    "source": RESULT_SOURCE,
                }
            )

    results.sort(key=lambda row: row["match_id"])
    return updated_fixtures, results


def load_fifa_matches(raw_file: Path | None = None) -> list[dict[str, Any]]:
    if raw_file is not None:
        payload = read_json(raw_file)
    else:
        response_text = fetch_text(FIFA_API_URL)
        payload = json.loads(response_text)
        write_json(FIFA_RAW_PATH, payload)
    results = payload.get("Results")
    if not isinstance(results, list):
        raise FetchError("FIFA API response missing Results list")
    return results


def sync_worldcup_data(raw_file: Path | None = None) -> dict[str, int]:
    fixtures_path = PROCESSED_DIR / "fixtures.json"
    teams_path = PROCESSED_DIR / "teams.json"
    groups_path = PROCESSED_DIR / "groups.json"
    results_path = PROCESSED_DIR / "results.json"

    for path in (fixtures_path, teams_path, groups_path):
        if not path.exists():
            raise FileNotFoundError(f"missing required processed file: {path}")

    fixtures = read_json(fixtures_path)
    teams = read_json(teams_path)
    groups = read_json(groups_path)
    fifa_matches = load_fifa_matches(raw_file)
    updated_fixtures, results = apply_fifa_updates(fixtures, fifa_matches)

    write_json(fixtures_path, updated_fixtures)
    write_json(results_path, results)
    write_json(teams_path, teams)
    write_json(groups_path, groups)

    return {
        "fifa_matches": len(fifa_matches),
        "fixtures_updated": len(updated_fixtures),
        "results_written": len(results),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sync World Cup 2026 fixtures/results from FIFA API v3."
    )
    parser.add_argument(
        "--raw-file",
        type=Path,
        help="Use a saved FIFA API JSON payload instead of fetching live data.",
    )
    args = parser.parse_args()

    try:
        summary = sync_worldcup_data(args.raw_file)
    except (FetchError, FileNotFoundError, json.JSONDecodeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(
        "Synced FIFA data at "
        f"{utc_now_iso()}: "
        f"{summary['results_written']} finished results, "
        f"{summary['fifa_matches']} FIFA matches inspected."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

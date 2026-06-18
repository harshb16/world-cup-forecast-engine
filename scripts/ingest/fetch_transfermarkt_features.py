"""Build computed squad features from the free Transfermarkt dataset."""

import argparse
import csv
import gzip
import json
import math
import re
import unicodedata
import urllib.request
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable
from difflib import get_close_matches

NATIONAL_TEAMS_URL = (
    "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/national_teams.csv.gz"
)
PLAYERS_URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/players.csv.gz"
PROCESSED_DIR = Path("data/processed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--national-teams-file", type=Path)
    parser.add_argument("--players-file", type=Path)
    parser.add_argument("--output", type=Path, default=PROCESSED_DIR / "squad_features.json")
    args = parser.parse_args()

    teams = _read_json(PROCESSED_DIR / "teams.json")
    national_teams = list(_read_csv(args.national_teams_file, NATIONAL_TEAMS_URL))
    players = list(_read_csv(args.players_file, PLAYERS_URL))

    national_by_key: dict[str, dict[str, str]] = {}
    for row in national_teams:
        for value in (row.get("name"), row.get("country_name")):
            key = _normalize(value or "")
            if key:
                national_by_key[key] = row
    national_keys = list(national_by_key)

    players_by_national_team: dict[str, list[dict[str, str]]] = defaultdict(list)
    for player in players:
        national_team_id = player.get("current_national_team_id")
        if national_team_id:
            players_by_national_team[national_team_id].append(player)

    features = []
    raw_rows = []
    for team in teams:
        national_team = _match_national_team(str(team["name"]), national_by_key, national_keys)
        player_rows = players_by_national_team.get(
            (national_team or {}).get("national_team_id", ""),
            [],
        )
        raw = _team_feature_row(team, national_team, player_rows)
        raw_rows.append(raw)

    for raw in raw_rows:
        features.append({**raw, "squad_power": round(_squad_power(raw), 1)})

    args.output.write_text(json.dumps(features, indent=2, ensure_ascii=False) + "\n")


def _read_csv(path: Path | None, url: str) -> Iterable[dict[str, str]]:
    with _open_csv_text(path, url) as file:
        yield from csv.DictReader(file)


@contextmanager
def _open_csv_text(path: Path | None, url: str):
    if path is not None:
        if path.suffix == ".gz":
            with gzip.open(path, "rt", newline="") as file:
                yield file
        else:
            with path.open(newline="") as file:
                yield file
        return

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "world-cup-oracle-data-ingest/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        with gzip.open(response, "rt", newline="") as file:
            yield file


def _team_feature_row(
    team: dict[str, object],
    national_team: dict[str, str] | None,
    players: list[dict[str, str]],
) -> dict[str, object]:
    team_rating = float(team["rating"])
    total_market_value = _float((national_team or {}).get("total_market_value"))
    average_age = _float((national_team or {}).get("average_age"))
    fifa_ranking = _float((national_team or {}).get("fifa_ranking"))

    if players:
        total_market_value = max(
            total_market_value,
            sum(_float(player.get("market_value_in_eur")) for player in players),
        )

    attack_value = _position_value(players, {"Attack"})
    midfield_value = _position_value(players, {"Midfield"})
    defense_value = _position_value(players, {"Defender", "Goalkeeper"})
    outfield_value = max(attack_value + midfield_value + defense_value, 1.0)

    return {
        "team_id": team["id"],
        "total_market_value": round(total_market_value, 1),
        "average_age": round(average_age, 1),
        "fifa_ranking": round(fifa_ranking, 1),
        "attack_bonus": round(45 * (attack_value / outfield_value - 0.33), 1),
        "defense_bonus": round(45 * (defense_value / outfield_value - 0.34), 1),
        "caps_signal": round(
            sum(_float(player.get("international_caps")) for player in players[:30]),
            1,
        ),
        "goals_signal": round(
            sum(_float(player.get("international_goals")) for player in players[:30]),
            1,
        ),
        "coverage": 1.0 if national_team else 0.0,
        "fallback_rating": team_rating,
    }


def _position_value(players: list[dict[str, str]], positions: set[str]) -> float:
    return sum(
        _float(player.get("market_value_in_eur"))
        for player in players
        if player.get("position") in positions
    )


def _squad_power(row: dict[str, object]) -> float:
    fallback_rating = float(row["fallback_rating"])
    market_value = float(row["total_market_value"])
    fifa_ranking = float(row["fifa_ranking"])

    market_power = fallback_rating
    if market_value > 0:
        market_power = 1000 + 140 * math.log10(max(market_value, 1))

    ranking_power = fallback_rating
    if fifa_ranking > 0:
        ranking_power = 2240 - (fifa_ranking - 1) * 8

    return (0.25 * fallback_rating) + (0.65 * market_power) + (0.10 * ranking_power)


def _float(value: str | None) -> float:
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except ValueError:
        return 0.0


def _normalize(value: str) -> str:
    value = "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    normalized = value.lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)
    normalized = normalized.replace("republic", "")
    return normalized


def _match_national_team(
    team_name: str,
    national_by_key: dict[str, dict[str, str]],
    national_keys: list[str],
) -> dict[str, str] | None:
    key = _normalize(team_name)
    if key in national_by_key:
        return national_by_key[key]

    for candidate in national_keys:
        if key and (key in candidate or candidate in key):
            return national_by_key[candidate]

    matches = get_close_matches(key, national_keys, n=1, cutoff=0.72)
    if matches:
        return national_by_key[matches[0]]
    return None


def _read_json(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError(f"expected list in {path}")
    return data


if __name__ == "__main__":
    main()

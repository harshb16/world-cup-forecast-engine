"""Train small open-data Elo parameters from international match results."""

from __future__ import annotations

import argparse
import csv
from io import StringIO
from pathlib import Path
from typing import Any

from common import PROCESSED_DIR, fetch_text, read_json, utc_now_iso, write_json

RESULTS_URL = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
START_DATE = "2018-01-01"
BASE_RATING = 1500.0
K_FACTOR = 28.0
HOME_ADVANTAGE = 55.0

TEAM_ALIASES = {
    "CIV": "Ivory Coast",
    "COD": "DR Congo",
    "CPV": "Cape Verde",
    "CZECHIA": "Czech Republic",
    "IRN": "Iran",
    "KOR": "South Korea",
    "RSA": "South Africa",
    "TURKIYE": "Turkey",
    "USA": "United States",
}


def train_open_elo(csv_text: str, active_teams: list[dict[str, Any]]) -> dict[str, Any]:
    ratings: dict[str, float] = {}
    rows = sorted(csv.DictReader(StringIO(csv_text)), key=lambda item: item["date"])

    for row in rows:
        if row["date"] < START_DATE:
            continue
        home_team = row["home_team"]
        away_team = row["away_team"]
        if not row["home_score"].isdigit() or not row["away_score"].isdigit():
            continue
        home_score = int(row["home_score"])
        away_score = int(row["away_score"])
        neutral = row["neutral"].upper() == "TRUE"

        ratings.setdefault(home_team, BASE_RATING)
        ratings.setdefault(away_team, BASE_RATING)

        home_rating = ratings[home_team] + (0 if neutral else HOME_ADVANTAGE)
        away_rating = ratings[away_team]
        expected_home = 1 / (1 + 10 ** ((away_rating - home_rating) / 400))
        actual_home = _actual_score(home_score, away_score)
        margin_multiplier = _margin_multiplier(abs(home_score - away_score))
        delta = K_FACTOR * margin_multiplier * (actual_home - expected_home)

        ratings[home_team] += delta
        ratings[away_team] -= delta

    return {
        "data_version": f"open-elo-{utc_now_iso()}",
        "source": {
            "name": "International football results from martj42/international_results",
            "url": RESULTS_URL,
            "usage": "Open-data Elo calibration from senior international match results.",
        },
        "training_window_start": START_DATE,
        "method": {
            "base_rating": BASE_RATING,
            "k_factor": K_FACTOR,
            "home_advantage": HOME_ADVANTAGE,
            "goal_margin_adjustment": "sqrt(goal_margin)",
        },
        "team_ratings": [
            {
                "team_id": team["id"],
                "team_name": team["name"],
                "source_team_name": _source_team_name(team),
                "rating": round(ratings.get(_source_team_name(team), team["rating"]), 1),
                "fallback_used": _source_team_name(team) not in ratings,
            }
            for team in active_teams
        ],
    }


def _actual_score(home_score: int, away_score: int) -> float:
    if home_score > away_score:
        return 1.0
    if home_score < away_score:
        return 0.0
    return 0.5


def _margin_multiplier(goal_margin: int) -> float:
    return max(goal_margin, 1) ** 0.5


def _source_team_name(team: dict[str, Any]) -> str:
    return TEAM_ALIASES.get(team["id"], team["name"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-file", type=Path)
    args = parser.parse_args()

    csv_text = (
        args.raw_file.read_text(encoding="utf-8")
        if args.raw_file
        else fetch_text(RESULTS_URL)
    )
    teams = read_json(PROCESSED_DIR / "teams.json")
    write_json(
        PROCESSED_DIR / "model_parameters.json",
        train_open_elo(csv_text, teams),
    )


if __name__ == "__main__":
    main()

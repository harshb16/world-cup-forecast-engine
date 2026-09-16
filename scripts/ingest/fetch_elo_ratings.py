"""Fetch or ingest World Football Elo ratings."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from common import FetchError, PROCESSED_DIR, fetch_text, read_json, write_json


ELO_RATINGS_URL = "https://www.eloratings.net/"


def parse_csv(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "team_id": row["team_id"],
                    "team_name": row["team_name"],
                    "elo_rating": int(float(row["elo_rating"])),
                    "source": "World Football Elo Ratings",
                }
            )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=ELO_RATINGS_URL)
    parser.add_argument("--raw-file", type=Path)
    args = parser.parse_args()

    if args.raw_file:
        ratings = (
            parse_csv(args.raw_file)
            if args.raw_file.suffix.lower() == ".csv"
            else read_json(args.raw_file)
        )
        write_json(PROCESSED_DIR / "ratings.json", ratings)
        return

    try:
        text = fetch_text(args.url)
    except FetchError as exc:
        raise SystemExit(
            f"{exc}\n"
            "Save normalized Elo ratings under data/raw/ratings/elo_ratings.csv "
            "or .json and rerun with --raw-file."
        )

    raw_path = Path("data/raw/ratings/elo_ratings_response.html")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(text, encoding="utf-8")
    raise SystemExit(
        "Remote Elo response saved for inspection. Convert ranking table to "
        "normalized CSV/JSON and rerun with --raw-file."
    )


if __name__ == "__main__":
    main()

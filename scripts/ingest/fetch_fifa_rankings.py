"""Fetch or ingest FIFA/Coca-Cola ranking data."""

from __future__ import annotations

import argparse
from pathlib import Path

from common import FetchError, PROCESSED_DIR, fetch_text, read_json, write_json


FIFA_RANKINGS_URL = "https://inside.fifa.com/fifa-world-ranking/men"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=FIFA_RANKINGS_URL)
    parser.add_argument("--raw-file", type=Path)
    args = parser.parse_args()

    if args.raw_file:
        payload = read_json(args.raw_file)
        if not isinstance(payload, list):
            raise SystemExit("ranking raw file must be a JSON list")
        write_json(PROCESSED_DIR / "ratings.json", payload)
        return

    try:
        text = fetch_text(args.url)
    except FetchError as exc:
        raise SystemExit(
            f"{exc}\n"
            "Save a normalized ranking list under data/raw/ratings/"
            "fifa_rankings.json and rerun with --raw-file."
        )

    raw_path = Path("data/raw/ratings/fifa_rankings_response.html")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(text, encoding="utf-8")
    raise SystemExit(
        "Remote FIFA ranking response saved for inspection. Convert embedded "
        "ranking data to normalized JSON and rerun with --raw-file."
    )


if __name__ == "__main__":
    main()

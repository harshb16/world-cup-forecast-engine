"""Fetch or ingest FIFA World Cup 2026 tournament data.

The preferred workflow is remote fetch from official FIFA URLs when those
responses are accessible. If FIFA blocks automated access or changes payloads,
save manually downloaded JSON/HTML under data/raw/fifa and run this script with
--raw-file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import FetchError, PROCESSED_DIR, fetch_text, read_json, write_json


FIFA_MATCH_CENTRE_URL = (
    "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/"
    "scores-fixtures"
)


def parse_normalized_payload(payload: dict[str, Any]) -> None:
    """Write an already-normalized raw payload to data/processed."""
    required = ["teams", "groups", "fixtures", "results"]
    missing = [key for key in required if key not in payload]
    if missing:
        raise ValueError(f"raw FIFA payload is missing keys: {', '.join(missing)}")

    for key in required:
        write_json(PROCESSED_DIR / f"{key}.json", payload[key])


def fetch_remote(url: str) -> str:
    return fetch_text(url)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=FIFA_MATCH_CENTRE_URL)
    parser.add_argument("--raw-file", type=Path)
    args = parser.parse_args()

    if args.raw_file:
        parse_normalized_payload(read_json(args.raw_file))
        return

    try:
        text = fetch_remote(args.url)
    except FetchError as exc:
        raise SystemExit(
            f"{exc}\n"
            "If FIFA blocks automated access, save a normalized raw payload to "
            "data/raw/fifa/worldcup_2026.json and rerun with --raw-file."
        )

    raw_path = Path("data/raw/fifa/worldcup_2026_response.txt")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(text, encoding="utf-8")
    raise SystemExit(
        "Remote FIFA response saved for inspection. Parse rules are intentionally "
        "not guessed; convert embedded FIFA JSON to normalized teams/groups/"
        "fixtures/results and rerun with --raw-file."
    )


if __name__ == "__main__":
    main()

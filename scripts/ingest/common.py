"""Shared helpers for World Cup data ingestion scripts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"


class FetchError(RuntimeError):
    """Raised when a remote source cannot be fetched."""


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def fetch_text(url: str, timeout: int = 20) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "WorldCupOracleDataBot/1.0 (+local development)",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise FetchError(f"failed to fetch {url}: {exc}") from exc


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()

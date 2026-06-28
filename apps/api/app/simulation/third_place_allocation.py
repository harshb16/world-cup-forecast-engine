"""FIFA 2026 third-place knockout slot allocation table."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
TABLE_PATH = REPO_ROOT / "data" / "tournament" / "third_place_allocations_2026.json"
SLOT_IDS = ("1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L")

_table_cache: dict[str, dict[str, str]] | None = None


def load_allocation_table() -> dict[str, dict[str, str]]:
    """Return qualified-group key to slot assignment map."""
    global _table_cache
    if _table_cache is not None:
        return _table_cache
    payload = json.loads(TABLE_PATH.read_text(encoding="utf-8"))
    _table_cache = {
        str(row["qualified_groups"]): dict(row["assignments"])
        for row in payload["rows"]
    }
    return _table_cache


def assign_third_place_slots(qualified_third_groups: set[str]) -> dict[str, str]:
    """Look up FIFA slot assignments for one third-place group combination."""
    if len(qualified_third_groups) != 8:
        raise ValueError("third-place allocation requires exactly eight groups")
    key = "".join(sorted(qualified_third_groups))
    try:
        return load_allocation_table()[key]
    except KeyError as exc:
        groups = ", ".join(sorted(qualified_third_groups))
        raise ValueError(f"unsupported third-place group combination: {groups}") from exc


def reset_allocation_table_cache_for_tests() -> None:
    """Clear cached allocation table."""
    global _table_cache
    _table_cache = None

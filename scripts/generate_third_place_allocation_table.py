"""Generate the 2026 FIFA third-place allocation lookup table."""

from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.simulation.knockout import GROUP_ORDER
from app.simulation.third_place_allocation import (
    SLOT_IDS,
    assign_third_place_slots as lookup_assign_third_place_slots,
)

# Backward-compatible alias used by the table generator.
_assign_third_place_slots = lookup_assign_third_place_slots
OUTPUT_PATH = REPO_ROOT / "data" / "tournament" / "third_place_allocations_2026.json"


def build_allocation_table() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for combo in combinations(GROUP_ORDER, 8):
        qualified_groups = set(combo)
        assignments = _assign_third_place_slots(qualified_groups)
        rows.append(
            {
                "qualified_groups": "".join(sorted(combo)),
                "assignments": assignments,
            }
        )
    return rows


def main() -> None:
    rows = build_allocation_table()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "format": "world_cup_2026",
                "row_count": len(rows),
                "rows": rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(rows)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

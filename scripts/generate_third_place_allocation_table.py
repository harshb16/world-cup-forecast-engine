"""Generate the 2026 FIFA third-place allocation lookup table from Annex C."""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ANNEX_C_ROWS_PATH = REPO_ROOT / "data" / "tournament" / "annex_c_rows.txt"
OUTPUT_PATH = REPO_ROOT / "data" / "tournament" / "third_place_allocations_2026.json"

# FIFA Annex C column order: group winner slot for each third-place assignment.
ANNEX_C_WINNER_SLOTS = ("1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L")


def load_annex_c_rows() -> list[str]:
    """Load the 495 official Annex C rows (one eight-letter string per line)."""
    lines = [
        line.strip()
        for line in ANNEX_C_ROWS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(lines) != 495:
        raise ValueError(f"expected 495 Annex C rows, found {len(lines)}")
    for index, row in enumerate(lines, start=1):
        if len(row) != 8:
            raise ValueError(f"Annex C row {index} must contain eight group letters")
        if len(set(row)) != 8:
            raise ValueError(f"Annex C row {index} contains duplicate group letters")
    return lines


def row_to_assignments(row: str) -> dict[str, str]:
    """Map one Annex C row to slot -> third-place group assignments."""
    return {
        slot_id: row[index]
        for index, slot_id in enumerate(ANNEX_C_WINNER_SLOTS)
    }


def build_allocation_table() -> list[dict[str, object]]:
    """Build lookup rows keyed by sorted qualifying third-place group letters."""
    rows: list[dict[str, object]] = []
    seen_keys: set[str] = set()

    for annex_row in load_annex_c_rows():
        assignments = row_to_assignments(annex_row)
        qualified_groups = "".join(sorted(assignments.values()))
        if qualified_groups in seen_keys:
            raise ValueError(f"duplicate Annex C combination key: {qualified_groups}")
        seen_keys.add(qualified_groups)
        rows.append(
            {
                "qualified_groups": qualified_groups,
                "assignments": assignments,
            }
        )

    expected_keys = {"".join(combo) for combo in combinations("ABCDEFGHIJKL", 8)}
    if seen_keys != expected_keys:
        missing = sorted(expected_keys - seen_keys)
        extra = sorted(seen_keys - expected_keys)
        raise ValueError(
            "Annex C rows do not cover all C(12,8) combinations: "
            f"missing={missing[:5]} extra={extra[:5]}"
        )

    return sorted(rows, key=lambda row: str(row["qualified_groups"]))


def main() -> None:
    rows = build_allocation_table()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            {
                "format": "world_cup_2026",
                "source": "FIFA FWC2026 Regulations Annex C (via annex_c_rows.txt)",
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

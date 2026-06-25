"""Tests for the FIFA 2026 third-place allocation lookup table."""

from __future__ import annotations

import json
from itertools import combinations

import pytest

from app.simulation.knockout import GROUP_ORDER

from app.simulation.third_place_allocation import (
    SLOT_IDS,
    TABLE_PATH,
    assign_third_place_slots,
    load_allocation_table,
)


def test_allocation_table_has_495_rows() -> None:
    payload = json.loads(TABLE_PATH.read_text(encoding="utf-8"))
    assert payload["row_count"] == 495
    assert len(payload["rows"]) == 495


def test_every_row_assigns_each_qualified_group_once() -> None:
    for row in load_allocation_table().values():
        assert set(row.values()) == set(row.values())  # sanity
        assert len(row) == len(SLOT_IDS)
        assert len(set(row.values())) == 8


@pytest.mark.parametrize(
    "qualified_groups",
    ["".join(groups) for groups in combinations(GROUP_ORDER, 8)],
)
def test_every_combination_has_lookup_row(qualified_groups: str) -> None:
    assignments = assign_third_place_slots(set(qualified_groups))
    assert set(assignments.values()) == set(qualified_groups)
    assert set(assignments) == set(SLOT_IDS)

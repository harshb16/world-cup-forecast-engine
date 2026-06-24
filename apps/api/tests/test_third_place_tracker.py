"""Tests for third-place qualification tracker aggregation."""

import pytest

from app.services.third_place_tracker_service import calculate_third_place_tracker


def test_third_place_tracker_accounts_for_all_eight_qualifiers() -> None:
    result = calculate_third_place_tracker(
        "sample",
        "oracle_v2",
        n_simulations=40,
        seed=7,
    )

    assert sum(
        team.qualification_probability for team in result.teams
    ) == pytest.approx(8.0)
    assert len(result.teams) > 12


def test_third_place_tracker_rejects_zero_simulations() -> None:
    with pytest.raises(ValueError, match="n_simulations must be at least 1"):
        calculate_third_place_tracker(
            "sample",
            "oracle_v2",
            n_simulations=0,
            seed=7,
        )

"""Tests for bank-derived plurality knockout brackets."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.bracket_service import plurality_bracket_from_bank
from app.services.data_loader import load_tournament
from app.services.simulation_bank_service import (
    build_simulation_bank,
    load_bank_arrays,
    modal_champion_and_final_pairing,
)
from app.simulation.bank_knockout_plurality import modal_qualifier_team_ids
from app.simulation.knockout import ADVANCEMENT_PAIRINGS, ROUND_NAMES


@pytest.fixture
def small_bank(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict[str, object]]:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "500")
    return build_simulation_bank(
        data_version="bank-plurality-test",
        n_simulations=500,
        master_seed=42,
        max_workers=1,
        batch_size=50,
    )


def test_plurality_bracket_from_bank_is_deterministic(
    small_bank: tuple[Path, dict[str, object]],
) -> None:
    bank_path, bank_meta = small_bank
    first = plurality_bracket_from_bank(bank_path, bank_meta, "processed")
    second = plurality_bracket_from_bank(bank_path, bank_meta, "processed")
    assert first == second


def test_plurality_bracket_metadata_and_mode(
    small_bank: tuple[Path, dict[str, object]],
) -> None:
    bank_path, bank_meta = small_bank
    bracket = plurality_bracket_from_bank(bank_path, bank_meta, "processed")
    assert bracket.simulation_mode == "bank_plurality"
    assert bracket.metadata.n_simulations == 500
    assert bracket.representative_simulation_index is None


def test_plurality_bracket_winners_align_with_advance_probabilities(
    small_bank: tuple[Path, dict[str, object]],
) -> None:
    bank_path, bank_meta = small_bank
    bracket = plurality_bracket_from_bank(bank_path, bank_meta, "processed")

    for matches in bracket.rounds.values():
        for match in matches:
            team_a_advance = match.probabilities.team_a_advance
            team_b_advance = match.probabilities.team_b_advance
            if team_a_advance > team_b_advance:
                assert match.winner_team_id == match.team_a.team_id
            elif team_b_advance > team_a_advance:
                assert match.winner_team_id == match.team_b.team_id
            else:
                winner_rating = (
                    match.team_a.rating
                    if match.winner_team_id == match.team_a.team_id
                    else match.team_b.rating
                )
                loser_rating = (
                    match.team_b.rating
                    if match.winner_team_id == match.team_a.team_id
                    else match.team_a.rating
                )
                assert winner_rating >= loser_rating


def test_plurality_bracket_matches_modal_champion_and_final(
    small_bank: tuple[Path, dict[str, object]],
) -> None:
    bank_path, bank_meta = small_bank
    bank = load_bank_arrays(bank_path)
    modal_champion_id, modal_runner_id = modal_champion_and_final_pairing(bank)
    bracket = plurality_bracket_from_bank(bank_path, bank_meta, "processed")

    assert bracket.champion_team_id == modal_champion_id
    final_match = bracket.rounds["Final"][0]
    assert {final_match.team_a.team_id, final_match.team_b.team_id} == {
        modal_champion_id,
        modal_runner_id,
    }


def test_plurality_bracket_tree_is_internally_consistent(
    small_bank: tuple[Path, dict[str, object]],
) -> None:
    bank_path, bank_meta = small_bank
    bracket = plurality_bracket_from_bank(bank_path, bank_meta, "processed")
    rounds = bracket.rounds

    for stage_index, stage in enumerate(ROUND_NAMES[1:], start=1):
        previous_stage = ROUND_NAMES[stage_index - 1]
        for match_number, match in enumerate(rounds[stage], start=1):
            pair_indices = ADVANCEMENT_PAIRINGS[stage][match_number - 1]
            feeders = [rounds[previous_stage][index] for index in pair_indices]
            feeder_winners = {
                feeder.winner_team_id
                for feeder in feeders
            }
            assert feeder_winners == {match.team_a.team_id, match.team_b.team_id}


def test_modal_qualifier_team_ids_are_valid(small_bank: tuple[Path, dict[str, object]]) -> None:
    bank_path, _bank_meta = small_bank
    bank = load_bank_arrays(bank_path)
    teams_by_id = {team.id: team for team in load_tournament("processed").teams}
    qualified_team_ids = modal_qualifier_team_ids(bank, teams_by_id)

    assert len(qualified_team_ids) == 32
    assert len(set(qualified_team_ids)) == 32

    for group_index, group_id in enumerate("ABCDEFGHIJKL"):
        winner_id = qualified_team_ids[group_index * 2]
        runner_up_id = qualified_team_ids[group_index * 2 + 1]
        assert teams_by_id[winner_id].group_id == group_id
        assert teams_by_id[runner_up_id].group_id == group_id

    third_place_ids = qualified_team_ids[24:]
    third_groups = {teams_by_id[team_id].group_id for team_id in third_place_ids}
    assert len(third_groups) == 8

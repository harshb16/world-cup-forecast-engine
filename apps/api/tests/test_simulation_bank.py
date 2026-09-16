"""Tests for snapshot simulation banks."""

from __future__ import annotations

import os

import numpy as np
import pytest

from app.services.simulation_bank_service import (
    BASELINE_SIMULATIONS,
    IN_PLAY_SIMULATIONS,
    build_simulation_bank,
    build_snapshot_seed,
    champion_probabilities_from_bank,
    champion_probabilities_match_summary,
    load_bank_arrays,
    simulation_summary_from_bank,
    simulation_summary_response_from_bank,
)
from app.services.team_path_service import team_path_from_bank
from app.simulation.knockout import ROUND_NAMES
from app.simulation.seed_sequence import SeedSequence


def test_seed_sequence_is_deterministic() -> None:
    sequence = SeedSequence(42)
    assert sequence.child_seed(0, 0) == sequence.child_seed(0, 0)
    assert sequence.child_seed(0, 0) != sequence.child_seed(0, 1)


def test_build_snapshot_seed_depends_on_data_and_model_versions() -> None:
    first = build_snapshot_seed(data_version="v1", model_version="calibrated_elo")
    second = build_snapshot_seed(data_version="v2", model_version="calibrated_elo")
    third = build_snapshot_seed(data_version="v1", model_version="poisson")
    assert first != second
    assert first != third


def test_build_simulation_bank_persists_npz_artifacts(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "200")
    bank_path, metadata = build_simulation_bank(
        data_version="test-version",
        n_simulations=200,
        master_seed=99,
        max_workers=2,
        batch_size=50,
    )
    assert bank_path.exists()
    assert metadata["n_simulations"] == 200
    payload = np.load(bank_path, allow_pickle=True)
    assert payload["champions"].shape == (200,)
    assert payload["qualified"].shape == (200, 48)
    assert payload["top_two"].shape == (200, 48)
    assert payload["third_finish"].shape == (200, 48)
    assert payload["third_qualified"].shape == (200, 48)
    assert payload["points"].shape == (200, 48)
    assert payload["max_stage"].shape == (200, 48)
    assert payload["qualifier_order"].shape == (200, 32)
    assert payload["knockout_opponents"].shape == (200, 48, 5)
    assert int(payload["batch_size"]) == 50
    assert metadata["batch_size"] == 50
    opponent_values = payload["knockout_opponents"]
    valid_mask = opponent_values >= 0
    assert np.all(opponent_values[valid_mask] < 48)
    assert np.all(opponent_values[~valid_mask] == -1)
    probabilities = champion_probabilities_from_bank(bank_path)
    assert pytest.approx(sum(probabilities.values()), rel=1e-6) == 1.0


def test_simulation_summary_from_bank_matches_champion_probabilities(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    bank_path, _ = build_simulation_bank(
        data_version="summary-test",
        n_simulations=120,
        master_seed=11,
        max_workers=1,
        batch_size=40,
    )
    summary = simulation_summary_from_bank(bank_path)
    champions = champion_probabilities_from_bank(bank_path)
    for team_id, probability in champions.items():
        assert summary.stage_probabilities[team_id]["champion"] == pytest.approx(probability)
    response = simulation_summary_response_from_bank(
        bank_path,
        data_mode="processed",
        model_type="elo",
        seed=11,
    )
    assert champion_probabilities_match_summary(response)


def test_team_path_from_bank_matches_opponent_trace(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    monkeypatch.setenv("WCO_SNAPSHOT_SIMULATIONS", "200")
    bank_path, bank_meta = build_simulation_bank(
        data_version="team-path-test",
        n_simulations=200,
        master_seed=42,
        max_workers=1,
        batch_size=50,
    )
    bank = load_bank_arrays(bank_path)
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    knockout_opponents: np.ndarray = bank["knockout_opponents"]  # type: ignore[assignment]
    team_id = team_ids[0]
    team_index = 0

    team_path = team_path_from_bank(
        bank_path,
        team_id,
        "processed",
        model_type=str(bank_meta["model_version"]),
        seed=int(bank_meta["master_seed"]),
    )
    assert team_path.metadata.n_simulations == 200

    for stage_index, stage_name in enumerate(ROUND_NAMES):
        expected_reached = int(np.sum(knockout_opponents[:, team_index, stage_index] >= 0))
        stage = next(item for item in team_path.stages if item.stage == stage_name)
        assert stage.reached_count == expected_reached
        if expected_reached > 0:
            assert stage.opponents
            assert stage.opponents[0].count <= expected_reached


def test_recommended_bank_sizes_match_tournament_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.simulation_bank_service import recommended_bank_size

    monkeypatch.delenv("WCO_SNAPSHOT_SIMULATIONS", raising=False)
    monkeypatch.setattr(
        "app.services.simulation_bank_service.is_tournament_active",
        lambda: False,
    )
    assert recommended_bank_size() == BASELINE_SIMULATIONS
    monkeypatch.setattr(
        "app.services.simulation_bank_service.is_tournament_active",
        lambda: True,
    )
    assert recommended_bank_size() == IN_PLAY_SIMULATIONS


@pytest.mark.slow
@pytest.mark.skipif(os.getenv("CI") == "true", reason="skip heavy bank perf in CI")
def test_large_bank_builds_within_target_budget(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import time

    monkeypatch.setenv("WCO_RUNTIME_DATA_DIR", str(tmp_path / "runtime"))
    started = time.perf_counter()
    bank_path, metadata = build_simulation_bank(
        data_version="perf-version",
        n_simulations=BASELINE_SIMULATIONS,
        master_seed=7,
        max_workers=4,
    )
    elapsed = time.perf_counter() - started
    assert bank_path.exists()
    assert metadata["n_simulations"] == BASELINE_SIMULATIONS
    assert elapsed < 240

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
)
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
    probabilities = champion_probabilities_from_bank(bank_path)
    assert pytest.approx(sum(probabilities.values()), rel=1e-6) == 1.0


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
    assert elapsed < 180

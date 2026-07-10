"""Offline replay artifact generator tests."""

from pathlib import Path
from unittest.mock import patch

from app.services.time_machine_generator import generate_time_machine_artifacts


def test_generator_writes_coherent_resumable_artifacts(tmp_path: Path) -> None:
    with patch("app.services.time_machine_generator.build_forecast_snapshot_from_bank") as build_snapshot, patch(
        "app.services.time_machine_generator.all_team_paths_from_bank", return_value={}
    ), patch("app.services.time_machine_generator.build_simulation_bank") as build_bank:
        from app.services.forecast_snapshot_service import load_forecast_snapshot

        bootstrap = load_forecast_snapshot()
        build_snapshot.return_value = bootstrap

        def fake_bank(**kwargs):
            path = kwargs["target_path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"bank")
            return path, {
                "model_version": kwargs["model_type"],
                "n_simulations": kwargs["n_simulations"],
                "master_seed": kwargs["master_seed"],
                "data_version": kwargs["data_version"],
            }

        build_bank.side_effect = fake_bank
        first = generate_time_machine_artifacts(
            n_simulations=2, target_root=tmp_path, progress=False
        )
        calls = build_bank.call_count
        second = generate_time_machine_artifacts(
            n_simulations=2, target_root=tmp_path, progress=False
        )

    assert first.data_version == second.data_version
    assert build_bank.call_count == calls
    available = [item for item in first.milestones if item.available]
    assert available
    for item in available:
        milestone_dir = tmp_path / "milestones" / item.id
        assert (milestone_dir / "snapshot.json").exists()
        assert (milestone_dir / "team_paths.json").exists()
        assert (milestone_dir / "bank.npz").exists()
        assert item.seed is not None
        assert item.checksum


def test_generator_require_complete_rejects_partial_tournament(tmp_path: Path) -> None:
    try:
        generate_time_machine_artifacts(
            n_simulations=1,
            target_root=tmp_path,
            require_complete=True,
            progress=False,
        )
    except RuntimeError as exc:
        assert "incomplete tournament milestones" in str(exc)
    else:
        raise AssertionError("partial tournament should not satisfy --require-complete")

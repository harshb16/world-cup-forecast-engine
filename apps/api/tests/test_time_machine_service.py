"""Milestone catalog and future-information leakage tests."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.models.domain import Group, Match, MatchResult, Team, TournamentConfig
from app.models.schemas import TimeMachineManifestResponse, TimeMachineMilestoneResponse
from app.services.time_machine_service import (
    MILESTONE_DEFINITIONS,
    derive_time_machine_seed,
    milestone_catalog,
    slice_tournament_at_milestone,
)


def _config() -> tuple[TournamentConfig, dict[str, dict]]:
    teams = [Team(id=f"T{i}", name=f"Team {i}", group_id="A", rating=1500) for i in range(1, 5)]
    group = Group(id="A", name="Group A", team_ids=[team.id for team in teams])
    played = MatchResult(team_a_goals=1, team_b_goals=0)
    matches = [
        Match(id="md1", stage="group", group_id="A", team_a_id="T1", team_b_id="T2", result=played),
        Match(id="md2", stage="group", group_id="A", team_a_id="T3", team_b_id="T4", result=played),
        Match(id="r32", stage="Round of 32", team_a_id="T1", team_b_id="T3", result=played, winner_team_id="T1"),
        Match(id="r16", stage="Round of 16", team_a_id="T1", team_b_id="T2", result=played, winner_team_id="T1"),
    ]
    raw = {
        "md1": {"kickoff_utc": "2026-06-11T18:00:00Z"},
        "md2": {"kickoff_utc": "2026-06-18T18:00:00Z"},
    }
    return TournamentConfig(teams=teams, groups=[group], matches=matches), raw


def test_exact_milestone_order_and_ids() -> None:
    assert [item.id for item in MILESTONE_DEFINITIONS] == [
        "before_group_md1", "after_group_md1", "after_group_md2", "after_group_md3",
        "after_round_of_32", "after_round_of_16", "after_quarter_finals",
        "after_semi_finals", "after_final",
    ]


def test_slice_hides_future_group_results_and_pairings() -> None:
    config, raw = _config()
    sliced = slice_tournament_at_milestone(config, raw, "after_group_md1")
    by_id = {match.id: match for match in sliced.matches}
    assert by_id["md1"].result is not None
    assert by_id["md2"].result is None
    assert "r32" not in by_id
    assert "r16" not in by_id


def test_slice_removes_later_knockout_pairings() -> None:
    config, raw = _config()
    sliced = slice_tournament_at_milestone(config, raw, "after_round_of_32")
    by_id = {match.id: match for match in sliced.matches}
    assert by_id["r32"].winner_team_id == "T1"
    assert "r16" not in by_id


def test_catalog_requires_complete_round() -> None:
    config, raw = _config()
    config.matches.append(Match(id="r32-pending", stage="Round of 32", team_a_id="T2", team_b_id="T4"))
    catalog = milestone_catalog(config, raw)
    assert catalog[1].available is True
    assert catalog[2].available is True
    assert catalog[4].available is False


def test_seed_is_deterministic_and_milestone_specific() -> None:
    first = derive_time_machine_seed("data-v1", "elo", "after_group_md1")
    assert first == derive_time_machine_seed("data-v1", "elo", "after_group_md1")
    assert first != derive_time_machine_seed("data-v1", "elo", "after_group_md2")


def test_group_fixture_sequence_handles_utc_schedule_boundaries() -> None:
    from app.services.time_machine_service import _group_matchday

    raw = {"J6": {"group_id": "J", "kickoff_utc": "2026-06-28T02:00:00Z"}}
    assert _group_matchday("J6", raw) == 3


def test_manifest_rejects_stale_data_version(tmp_path: Path) -> None:
    manifest = TimeMachineManifestResponse(
        data_version="old-data",
        model_version="elo",
        simulation_count=1,
        milestones=[],
    )
    (tmp_path / "manifest.json").write_text(manifest.model_dump_json())
    from app.services.time_machine_service import load_time_machine_manifest

    with patch("app.services.time_machine_service.get_time_machine_root", return_value=tmp_path), patch(
        "app.services.time_machine_service.load_metadata",
        return_value={"data_version": "new-data"},
    ), pytest.raises(RuntimeError, match="stale"):
        load_time_machine_manifest()


def test_snapshot_rejects_corrupt_json(tmp_path: Path) -> None:
    milestone = TimeMachineMilestoneResponse(
        id="before_group_md1",
        label="Before Matchday 1",
        order=0,
        phase="pre_tournament",
        cutoff="group_md0",
        known_result_count=0,
        available=True,
    )
    manifest = TimeMachineManifestResponse(
        data_version="data-v1",
        model_version="elo",
        simulation_count=1,
        milestones=[milestone],
    )
    (tmp_path / "manifest.json").write_text(manifest.model_dump_json())
    artifact_dir = tmp_path / "milestones" / milestone.id
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "snapshot.json").write_text("{not-json")
    from app.services.time_machine_service import load_time_machine_snapshot

    with patch("app.services.time_machine_service.get_time_machine_root", return_value=tmp_path), patch(
        "app.services.time_machine_service.load_metadata",
        return_value={"data_version": "data-v1"},
    ), pytest.raises(ValueError):
        load_time_machine_snapshot(milestone.id)

"""Milestone catalog and future-information leakage tests."""

from app.models.domain import Group, Match, MatchResult, Team, TournamentConfig
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

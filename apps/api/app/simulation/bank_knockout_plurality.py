"""Build a plurality knockout tree from stored simulation bank arrays."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.models.domain import KnockoutResult, Match, MatchResult, Team
from app.simulation.knockout import (
    ADVANCEMENT_PAIRINGS,
    GROUP_ORDER,
    ROUND_NAMES,
    WorldCup2026BracketBuilder,
    _pair_by_indices,
    _round_code,
)

QUALIFIER_COUNT = 32
FINAL_ROUND_INDEX = len(ROUND_NAMES) - 1


@dataclass(frozen=True)
class KnockoutMatchupStats:
    """Bank-derived head-to-head stats for one knockout pairing."""

    support: int
    team_a_wins: int
    team_a_advance: float
    team_b_advance: float
    winner_team_id: str
    used_model_fallback: bool


@dataclass(frozen=True)
class PluralityKnockoutBuild:
    """Knockout tree plus per-match bank advance probabilities."""

    knockout: KnockoutResult
    advance_probabilities: dict[str, tuple[float, float]]


def min_matchup_support(n_simulations: int) -> int:
    """Minimum bank support before falling back to model probabilities."""
    return max(1, n_simulations // 1000)


def modal_qualifier_team_ids(
    bank: dict[str, np.ndarray | list[str] | int],
    teams_by_id: dict[str, Team],
) -> list[str]:
    """Return modal 32-team qualifier order from bank qualifier_order slots."""
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    qualifier_order: np.ndarray = bank["qualifier_order"]  # type: ignore[assignment]
    qualified: np.ndarray = bank["qualified"]  # type: ignore[assignment]
    top_two: np.ndarray = bank["top_two"]  # type: ignore[assignment]
    third_qualified: np.ndarray = bank["third_qualified"]  # type: ignore[assignment]
    team_count = len(team_ids)

    modal_indices = [
        _modal_team_index_for_slot(
            qualifier_order[:, slot],
            team_count=team_count,
            qualified=qualified,
            top_two=top_two,
            third_qualified=third_qualified,
            teams_by_id=teams_by_id,
            team_ids=team_ids,
            slot=slot,
        )
        for slot in range(QUALIFIER_COUNT)
    ]
    modal_ids = [team_ids[index] for index in modal_indices]

    if _qualifier_order_is_valid(modal_ids, teams_by_id):
        return modal_ids

    return _repair_qualifier_team_ids(
        bank,
        teams_by_id=teams_by_id,
        team_ids=team_ids,
    )


def knockout_matchup_stats(
    bank: dict[str, np.ndarray | list[str] | int],
    *,
    team_a_id: str,
    team_b_id: str,
    round_index: int,
    teams_by_id: dict[str, Team],
    model_advance_probability,
    modal_champion_id: str | None = None,
    modal_runner_id: str | None = None,
) -> KnockoutMatchupStats:
    """Aggregate bank win rates for one knockout pairing at a round."""
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    qualified: np.ndarray = bank["qualified"]  # type: ignore[assignment]
    knockout_opponents: np.ndarray = bank["knockout_opponents"]  # type: ignore[assignment]
    champions: np.ndarray = bank["champions"]  # type: ignore[assignment]
    n_simulations: int = bank["n_simulations"]  # type: ignore[assignment]

    team_a_index = team_ids.index(team_a_id)
    team_b_index = team_ids.index(team_b_id)
    met = (
        qualified[:, team_a_index]
        & qualified[:, team_b_index]
        & (knockout_opponents[:, team_a_index, round_index] == team_b_index)
        & (knockout_opponents[:, team_b_index, round_index] == team_a_index)
    )
    if round_index < FINAL_ROUND_INDEX:
        team_a_won = met & (knockout_opponents[:, team_a_index, round_index + 1] >= 0)
    else:
        team_a_won = met & (champions == team_a_index)

    support = int(met.sum())
    wins_a = int(team_a_won.sum())
    threshold = min_matchup_support(n_simulations)

    if support < threshold:
        team_a = teams_by_id[team_a_id]
        team_b = teams_by_id[team_b_id]
        team_a_advance = float(model_advance_probability(team_a, team_b))
        team_b_advance = 1.0 - team_a_advance
        if team_a_advance >= team_b_advance:
            winner_team_id = team_a_id
        elif team_b_advance > team_a_advance:
            winner_team_id = team_b_id
        else:
            winner_team_id = _rating_tiebreak_winner(team_a, team_b)
        return KnockoutMatchupStats(
            support=support,
            team_a_wins=wins_a,
            team_a_advance=team_a_advance,
            team_b_advance=team_b_advance,
            winner_team_id=winner_team_id,
            used_model_fallback=True,
        )

    modal_pair = (
        modal_champion_id is not None
        and modal_runner_id is not None
        and {team_a_id, team_b_id} == {modal_champion_id, modal_runner_id}
    )
    if modal_pair:
        champion_counts = np.bincount(champions, minlength=len(team_ids))
        score_a = float(champion_counts[team_a_index])
        score_b = float(champion_counts[team_b_index])
        total = score_a + score_b
        if total <= 0:
            team_a_advance = 0.5
        else:
            team_a_advance = score_a / total
        team_b_advance = 1.0 - team_a_advance
        if score_a > score_b:
            winner_team_id = team_a_id
        elif score_b > score_a:
            winner_team_id = team_b_id
        else:
            winner_team_id = _rating_tiebreak_winner(
                teams_by_id[team_a_id],
                teams_by_id[team_b_id],
            )
        return KnockoutMatchupStats(
            support=support,
            team_a_wins=wins_a,
            team_a_advance=team_a_advance,
            team_b_advance=team_b_advance,
            winner_team_id=winner_team_id,
            used_model_fallback=False,
        )

    champion_counts = np.bincount(champions, minlength=len(team_ids))
    finalist_counts = np.sum(knockout_opponents[:, :, FINAL_ROUND_INDEX] >= 0, axis=0)
    wins_b = support - wins_a
    score_a = wins_a + champion_counts[team_a_index] + finalist_counts[team_a_index]
    score_b = wins_b + champion_counts[team_b_index] + finalist_counts[team_b_index]
    score_total = score_a + score_b
    team_a_advance = score_a / score_total if score_total > 0 else 0.5
    team_b_advance = 1.0 - team_a_advance
    if score_a > score_b:
        winner_team_id = team_a_id
    elif score_b > score_a:
        winner_team_id = team_b_id
    else:
        winner_team_id = _rating_tiebreak_winner(
            teams_by_id[team_a_id],
            teams_by_id[team_b_id],
        )
    return KnockoutMatchupStats(
        support=support,
        team_a_wins=wins_a,
        team_a_advance=team_a_advance,
        team_b_advance=team_b_advance,
        winner_team_id=winner_team_id,
        used_model_fallback=False,
    )


def build_plurality_knockout(
    bank: dict[str, np.ndarray | list[str] | int],
    *,
    qualified_team_ids: list[str],
    teams_by_id: dict[str, Team],
    model_advance_probability,
    projected_result,
    modal_champion_id: str | None = None,
    modal_runner_id: str | None = None,
) -> PluralityKnockoutBuild:
    """Build a knockout tree using bank plurality winners round by round."""
    builder = WorldCup2026BracketBuilder()
    rounds: dict[str, list[Match]] = {}
    advance_probabilities: dict[str, tuple[float, float]] = {}
    eliminated_stage_by_team: dict[str, str] = {}
    finalists: list[str] = []

    current_team_ids = list(qualified_team_ids)
    for round_name in ROUND_NAMES:
        round_index = ROUND_NAMES.index(round_name)
        if round_name == "Round of 32":
            pairs = builder.build_round_of_32(current_team_ids, teams_by_id)
        else:
            pairs = _pair_by_indices(current_team_ids, ADVANCEMENT_PAIRINGS[round_name])

        if round_name == "Final":
            finalists = list(current_team_ids)

        round_matches: list[Match] = []
        winners: list[str] = []
        for index, (team_a_id, team_b_id) in enumerate(pairs, start=1):
            stats = knockout_matchup_stats(
                bank,
                team_a_id=team_a_id,
                team_b_id=team_b_id,
                round_index=round_index,
                teams_by_id=teams_by_id,
                model_advance_probability=model_advance_probability,
                modal_champion_id=modal_champion_id,
                modal_runner_id=modal_runner_id,
            )
            winner_team_id = stats.winner_team_id
            team_a_advance = stats.team_a_advance
            team_b_advance = stats.team_b_advance
            if (
                round_index < FINAL_ROUND_INDEX
                and modal_champion_id is not None
                and modal_champion_id in {team_a_id, team_b_id}
            ):
                winner_team_id = modal_champion_id
            elif (
                round_index < FINAL_ROUND_INDEX
                and modal_runner_id is not None
                and modal_runner_id in {team_a_id, team_b_id}
                and modal_champion_id not in {team_a_id, team_b_id}
            ):
                winner_team_id = modal_runner_id
            if winner_team_id != stats.winner_team_id:
                if winner_team_id == team_a_id:
                    team_a_advance = max(team_a_advance, team_b_advance + 0.01, 0.51)
                    team_b_advance = 1.0 - team_a_advance
                else:
                    team_b_advance = max(team_b_advance, team_a_advance + 0.01, 0.51)
                    team_a_advance = 1.0 - team_b_advance
            team_a = teams_by_id[team_a_id]
            team_b = teams_by_id[team_b_id]
            result = projected_result(team_a, team_b, winner_team_id)
            loser_team_id = team_b_id if winner_team_id == team_a_id else team_a_id
            eliminated_stage_by_team[loser_team_id] = round_name
            winners.append(winner_team_id)
            match_id = f"KO-{_round_code(round_name)}-{index:02d}"
            round_matches.append(
                Match(
                    id=match_id,
                    stage=round_name,
                    team_a_id=team_a_id,
                    team_b_id=team_b_id,
                    result=result,
                    winner_team_id=winner_team_id,
                )
            )
            advance_probabilities[match_id] = (
                team_a_advance,
                team_b_advance,
            )

        rounds[round_name] = round_matches
        current_team_ids = winners

    champion_team_id = current_team_ids[0]
    eliminated_stage_by_team[champion_team_id] = "Champion"

    return PluralityKnockoutBuild(
        knockout=KnockoutResult(
            rounds=rounds,
            eliminated_stage_by_team=eliminated_stage_by_team,
            finalists=finalists,
            champion_team_id=champion_team_id,
        ),
        advance_probabilities=advance_probabilities,
    )


def _modal_team_index_for_slot(
    slot_values: np.ndarray,
    *,
    team_count: int,
    qualified: np.ndarray,
    top_two: np.ndarray,
    third_qualified: np.ndarray,
    teams_by_id: dict[str, Team],
    team_ids: list[str],
    slot: int,
) -> int:
    valid = slot_values[slot_values >= 0]
    if valid.size == 0:
        return 0
    counts = np.bincount(valid, minlength=team_count)
    max_count = counts.max()
    candidates = np.flatnonzero(counts == max_count)
    if candidates.size == 1:
        return int(candidates[0])

    def sort_key(team_index: int) -> tuple[float, float, float, float, str]:
        team_id = team_ids[team_index]
        qualification_rate = float(np.mean(qualified[:, team_index]))
        top_two_rate = float(np.mean(top_two[:, team_index]))
        third_rate = float(np.mean(third_qualified[:, team_index]))
        rating = teams_by_id[team_id].rating
        return (qualification_rate, top_two_rate, third_rate, rating, team_id)

    return int(max(candidates, key=sort_key))


def _qualifier_order_is_valid(
    qualified_team_ids: list[str],
    teams_by_id: dict[str, Team],
) -> bool:
    if len(qualified_team_ids) != QUALIFIER_COUNT:
        return False
    if len(set(qualified_team_ids)) != QUALIFIER_COUNT:
        return False

    for group_index, group_id in enumerate(GROUP_ORDER):
        winner_id = qualified_team_ids[group_index * 2]
        runner_up_id = qualified_team_ids[group_index * 2 + 1]
        if teams_by_id[winner_id].group_id != group_id:
            return False
        if teams_by_id[runner_up_id].group_id != group_id:
            return False

    third_place_ids = qualified_team_ids[24:]
    third_groups = {teams_by_id[team_id].group_id for team_id in third_place_ids}
    return len(third_groups) == 8


def _repair_qualifier_team_ids(
    bank: dict[str, np.ndarray | list[str] | int],
    *,
    teams_by_id: dict[str, Team],
    team_ids: list[str],
) -> list[str]:
    """Rebuild a valid qualifier order from bank qualification frequencies."""
    top_two: np.ndarray = bank["top_two"]  # type: ignore[assignment]
    third_qualified: np.ndarray = bank["third_qualified"]  # type: ignore[assignment]
    team_count = len(team_ids)

    repaired: list[str] = []
    used: set[str] = set()
    for group_id in GROUP_ORDER:
        group_team_ids = [
            team.id for team in teams_by_id.values() if team.group_id == group_id
        ]
        ranked = sorted(
            group_team_ids,
            key=lambda team_id: (
                float(np.mean(top_two[:, team_ids.index(team_id)])),
                teams_by_id[team_id].rating,
                team_id,
            ),
            reverse=True,
        )
        winner_id = next(team_id for team_id in ranked if team_id not in used)
        used.add(winner_id)
        runner_up_id = next(team_id for team_id in ranked if team_id not in used)
        used.add(runner_up_id)
        repaired.extend([winner_id, runner_up_id])

    third_candidates = sorted(
        range(team_count),
        key=lambda team_index: (
            float(np.mean(third_qualified[:, team_index])),
            teams_by_id[team_ids[team_index]].rating,
            team_ids[team_index],
        ),
        reverse=True,
    )
    third_place_ids: list[str] = []
    third_groups: set[str] = set()
    for team_index in third_candidates:
        team_id = team_ids[team_index]
        if team_id in used:
            continue
        group_id = teams_by_id[team_id].group_id
        if group_id in third_groups:
            continue
        third_place_ids.append(team_id)
        third_groups.add(group_id)
        used.add(team_id)
        if len(third_place_ids) == 8:
            break

    if len(third_place_ids) != 8:
        raise ValueError("unable to repair modal qualifier order from bank")

    repaired.extend(third_place_ids)
    return repaired


def _rating_tiebreak_winner(team_a: Team, team_b: Team) -> str:
    if team_a.rating > team_b.rating:
        return team_a.id
    if team_b.rating > team_a.rating:
        return team_b.id
    return team_a.id if team_a.id <= team_b.id else team_b.id


def projected_result_for_winner(
    match_model,
    team_a: Team,
    team_b: Team,
    winner_team_id: str,
) -> MatchResult:
    """Return a synthetic scoreline for the chosen knockout winner."""
    base_result = match_model.projected_result(team_a, team_b)
    if winner_team_id == team_a.id:
        if base_result.team_a_goals <= base_result.team_b_goals:
            margin = 1 if base_result.team_a_goals == base_result.team_b_goals else 0
            return MatchResult(
                team_a_goals=base_result.team_b_goals + 1 + margin,
                team_b_goals=base_result.team_b_goals,
            )
        return base_result
    if base_result.team_b_goals <= base_result.team_a_goals:
        margin = 1 if base_result.team_a_goals == base_result.team_b_goals else 0
        return MatchResult(
            team_a_goals=base_result.team_a_goals,
            team_b_goals=base_result.team_a_goals + 1 + margin,
        )
    return base_result

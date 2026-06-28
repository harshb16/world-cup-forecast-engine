"""Bracket trace service for interactive tournament reveals."""

from pathlib import Path

import numpy as np

from app.models.domain import (
    GroupStageResult,
    Match,
    MatchResult,
    Team,
    TournamentConfig,
)
from app.models.schemas import (
    BracketGroupTableResponse,
    BracketMatchProbabilityResponse,
    BracketMatchResponse,
    BracketSimulateRequest,
    BracketSimulationResponse,
    BracketTeamResponse,
    SimulationMetadataResponse,
)
from app.services.data_loader import load_metadata, load_tournament
from app.services.simulation_bank_service import (
    load_bank_arrays,
    modal_champion_and_final_pairing,
)
from app.services.simulation_service import apply_result_overrides, create_match_model
from app.simulation.bank_knockout_plurality import (
    build_plurality_knockout,
    modal_qualifier_team_ids,
    projected_result_for_winner,
)
from app.simulation.group_stage import simulate_group_stage
from app.simulation.group_table import calculate_group_table
from app.simulation.knockout import ADVANCEMENT_PAIRINGS, ROUND_NAMES, simulate_knockout
from app.simulation.knockout_resolution import with_host_advantage
from app.simulation.match_models import MatchModel
from app.simulation.third_place import get_best_third_place_qualifiers, rank_third_place_teams


def plurality_bracket_from_bank(
    bank_path: Path,
    bank_meta: dict[str, object],
    data_mode: str,
) -> BracketSimulationResponse:
    """Build a bank plurality knockout tree for publish and snapshot reads."""
    bank = load_bank_arrays(bank_path)
    model_type = str(bank_meta["model_version"])
    base_config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in base_config.teams}
    base_match_model = create_match_model(model_type, data_mode)  # type: ignore[arg-type]
    match_model = _MostLikelyMatchModel(base_match_model)
    qualified_team_ids = modal_qualifier_team_ids(bank, teams_by_id)
    modal_champion_id, modal_runner_id = modal_champion_and_final_pairing(bank)
    group_stage = _hybrid_group_stage_from_bank(
        base_config,
        match_model,
        modal_qualified_team_ids=qualified_team_ids,
    )
    qualified_team_ids = group_stage.qualified_team_ids
    plurality = build_plurality_knockout(
        bank,
        qualified_team_ids=qualified_team_ids,
        teams_by_id=teams_by_id,
        model_advance_probability=match_model._team_a_advance_probability,
        projected_result=lambda team_a, team_b, winner_team_id: projected_result_for_winner(
            match_model,
            team_a,
            team_b,
            winner_team_id,
        ),
        modal_champion_id=modal_champion_id,
        modal_runner_id=modal_runner_id,
    )
    knockout = plurality.knockout
    metadata = SimulationMetadataResponse(
        n_simulations=int(bank_meta["n_simulations"]),
        model_type=model_type,  # type: ignore[arg-type]
        seed=int(bank_meta["master_seed"]),
        overrides_applied=[],
        **load_metadata(data_mode),
    )
    champion = teams_by_id[knockout.champion_team_id]
    completed_groups = _completed_group_ids(base_config)

    return BracketSimulationResponse(
        metadata=metadata,
        simulation_mode="bank_plurality",
        group_tables=[
            BracketGroupTableResponse(
                group_id=group_id,
                rows=[row.model_dump() for row in rows],
            )
            for group_id, rows in group_stage.group_tables.items()
        ],
        rounds={
            stage: [
                _to_bracket_match(
                    match,
                    teams_by_id,
                    match_model,
                    index,
                    _source_match_ids(knockout.rounds, match, index),
                    completed_groups=completed_groups,
                    advance_probabilities=plurality.advance_probabilities.get(match.id),
                )
                for index, match in enumerate(matches, start=1)
            ]
            for stage, matches in knockout.rounds.items()
        },
        champion_team_id=champion.id,
        champion_team_name=champion.name,
        representative_simulation_index=None,
    )


def representative_bracket_from_bank(
    bank_path: Path,
    bank_meta: dict[str, object],
    data_mode: str,
) -> BracketSimulationResponse:
    """Replay one representative bank simulation as a full bracket trace."""
    from app.services.simulation_bank_service import representative_child_seed

    bank = load_bank_arrays(bank_path)
    rep_index, child_seed = representative_child_seed(
        bank,
        int(bank_meta["master_seed"]),
    )
    model_type = str(bank_meta["model_version"])
    response = run_bracket_simulation(
        BracketSimulateRequest(
            model_type=model_type,  # type: ignore[arg-type]
            simulation_mode="random",
            seed=child_seed,
        ),
        data_mode,
    )
    return response.model_copy(
        update={
            "simulation_mode": "bank_representative",
            "metadata": response.metadata.model_copy(
                update={
                    "n_simulations": int(bank_meta["n_simulations"]),
                    "seed": child_seed,
                }
            ),
            "representative_simulation_index": rep_index,
        }
    )


def run_bracket_simulation(
    request: BracketSimulateRequest,
    data_mode: str,
) -> BracketSimulationResponse:
    """Run one tournament trace for client-side bracket reveal."""
    base_config = load_tournament(data_mode)
    config = apply_result_overrides(base_config, request.result_overrides)
    teams_by_id = {team.id: team for team in config.teams}
    base_match_model = create_match_model(request.model_type, data_mode)
    match_model = (
        _MostLikelyMatchModel(base_match_model)
        if request.simulation_mode == "favorite"
        else base_match_model
    )
    rng = np.random.default_rng(request.seed)

    if request.simulation_mode == "favorite":
        if request.result_overrides:
            group_stage = simulate_group_stage(config, match_model, rng)
        else:
            group_stage = _project_favorite_group_stage(config, match_model)
    else:
        group_stage = simulate_group_stage(config, match_model, rng)
    knockout = simulate_knockout(
        group_stage.qualified_team_ids,
        teams_by_id,
        match_model,
        rng,
    )
    metadata = SimulationMetadataResponse(
        n_simulations=1,
        model_type=request.model_type,
        seed=request.seed,
        overrides_applied=request.result_overrides,
        **load_metadata(data_mode),
    )
    champion = teams_by_id[knockout.champion_team_id]
    completed_groups = _completed_group_ids(config)

    return BracketSimulationResponse(
        metadata=metadata,
        simulation_mode=request.simulation_mode,
        group_tables=[
            BracketGroupTableResponse(
                group_id=group_id,
                rows=[row.model_dump() for row in rows],
            )
            for group_id, rows in group_stage.group_tables.items()
        ],
        rounds={
            stage: [
                _to_bracket_match(
                    match,
                    teams_by_id,
                    match_model,
                    index,
                    _source_match_ids(knockout.rounds, match, index),
                    completed_groups=completed_groups,
                )
                for index, match in enumerate(matches, start=1)
            ]
            for stage, matches in knockout.rounds.items()
        },
        champion_team_id=champion.id,
        champion_team_name=champion.name,
    )


def _to_bracket_match(
    match: Match,
    teams_by_id: dict[str, Team],
    match_model,
    match_number: int,
    source_match_ids: list[str],
    completed_groups: set[str] | None = None,
    advance_probabilities: tuple[float, float] | None = None,
) -> BracketMatchResponse:
    team_a = teams_by_id[match.team_a_id]
    team_b = teams_by_id[match.team_b_id]
    probability_team_a = with_host_advantage(team_a) if match.stage != "group" else team_a
    probability_team_b = with_host_advantage(team_b) if match.stage != "group" else team_b
    probabilities = match_model.predict_probabilities(probability_team_a, probability_team_b)
    if advance_probabilities is None:
        team_a_rating = _model_rating(match_model, probability_team_a)
        team_b_rating = _model_rating(match_model, probability_team_b)
        team_a_tiebreak = 1 / (1 + 10 ** (-(team_a_rating - team_b_rating) / 400))
        team_a_advance = (
            probabilities["team_a_win"] + probabilities["draw"] * team_a_tiebreak
        )
        team_b_advance = probabilities["team_b_win"] + probabilities["draw"] * (
            1 - team_a_tiebreak
        )
    else:
        team_a_advance, team_b_advance = advance_probabilities
    expected_goals = _expected_goals(match_model, probability_team_a, probability_team_b)

    if match.result is None or match.winner_team_id is None:
        raise ValueError("bracket trace match must include result and winner")

    completed = completed_groups or set()
    confirmed = (
        match.stage == "Round of 32"
        and team_a.group_id in completed
        and team_b.group_id in completed
    )

    return BracketMatchResponse(
        id=match.id,
        stage=match.stage,
        match_number=match_number,
        source_match_ids=source_match_ids,
        team_a=_to_bracket_team(team_a),
        team_b=_to_bracket_team(team_b),
        result={
            "team_a_goals": match.result.team_a_goals,
            "team_b_goals": match.result.team_b_goals,
        },
        winner_team_id=match.winner_team_id,
        probabilities=BracketMatchProbabilityResponse(
            team_a_win=probabilities["team_a_win"],
            draw=probabilities["draw"],
            team_b_win=probabilities["team_b_win"],
            team_a_advance=team_a_advance,
            team_b_advance=team_b_advance,
        ),
        team_a_expected_goals=expected_goals[0],
        team_b_expected_goals=expected_goals[1],
        confidence_label=_confidence_label(max(team_a_advance, team_b_advance)),
        drivers=_match_drivers(match_model, team_a, team_b),
        confirmed=confirmed,
    )


def _completed_group_ids(config: TournamentConfig) -> set[str]:
    """Return group ids where every group fixture has a played result."""
    group_match_counts: dict[str, int] = {}
    group_played_counts: dict[str, int] = {}
    for match in config.matches:
        if match.stage != "group" or match.group_id is None:
            continue
        group_match_counts[match.group_id] = group_match_counts.get(match.group_id, 0) + 1
        if match.result is not None and match.result.played:
            group_played_counts[match.group_id] = group_played_counts.get(match.group_id, 0) + 1
    return {
        group_id
        for group_id, total in group_match_counts.items()
        if group_played_counts.get(group_id, 0) == total
    }


def _source_match_ids(
    rounds: dict[str, list[Match]],
    match: Match,
    match_number: int,
) -> list[str]:
    round_index = ROUND_NAMES.index(match.stage)
    if round_index == 0:
        return []

    previous_round = ROUND_NAMES[round_index - 1]
    pair_indices = ADVANCEMENT_PAIRINGS[match.stage][match_number - 1]
    previous_matches = rounds[previous_round]
    return [previous_matches[index].id for index in pair_indices]


def _to_bracket_team(team: Team) -> BracketTeamResponse:
    return BracketTeamResponse(
        team_id=team.id,
        team_name=team.name,
        group_id=team.group_id,
        rating=team.rating,
    )


def _expected_goals(
    match_model,
    team_a: Team,
    team_b: Team,
) -> tuple[float | None, float | None]:
    expected_goals = getattr(match_model, "expected_goals", None)
    if callable(expected_goals):
        team_a_expected, team_b_expected = expected_goals(team_a, team_b)
        return round(float(team_a_expected), 2), round(float(team_b_expected), 2)

    base_model = getattr(match_model, "base_model", None)
    base_expected_goals = getattr(base_model, "expected_goals", None)
    if callable(base_expected_goals):
        team_a_expected, team_b_expected = base_expected_goals(team_a, team_b)
        return round(float(team_a_expected), 2), round(float(team_b_expected), 2)

    return None, None


def _confidence_label(advance_probability: float) -> str:
    if advance_probability >= 0.68:
        return "clear favorite"
    if advance_probability >= 0.58:
        return "lean"
    return "coin flip"


def _match_drivers(match_model, team_a: Team, team_b: Team) -> list[str]:
    rating_gap = abs(_model_rating(match_model, team_a) - _model_rating(match_model, team_b))
    drivers = ["rating blend"]
    if rating_gap >= 120:
        drivers.append("strength gap")
    if _expected_goals(match_model, team_a, team_b) != (None, None):
        drivers.append("xG proxy")
    return drivers[:3]


class _MostLikelyMatchModel:
    """Deterministic projection wrapper for a human-readable favorite bracket."""

    def __init__(self, base_model: MatchModel) -> None:
        self.base_model = base_model

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        rating_gap = self.rating_for(team_a) - self.rating_for(team_b)
        expected_a = 1 / (1 + 10 ** (-rating_gap / 400))
        draw_probability = max(0.12, 0.24 - min(abs(rating_gap) / 2200, 0.1))
        decisive_probability = 1 - draw_probability

        return {
            "team_a_win": decisive_probability * expected_a,
            "draw": draw_probability,
            "team_b_win": decisive_probability * (1 - expected_a),
        }

    def rating_for(self, team: Team) -> float:
        return _base_model_rating(self.base_model, team)

    def projected_result(self, team_a: Team, team_b: Team) -> MatchResult:
        projected_result = getattr(self.base_model, "projected_result", None)
        if callable(projected_result):
            return projected_result(team_a, team_b)
        return self.simulate_result(team_a, team_b, np.random.default_rng(0))

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
        stage: str | None = None,
    ) -> MatchResult:
        probabilities = self.predict_probabilities(team_a, team_b)
        if stage == "extra_time":
            favorite_is_a = self._team_a_advance_probability(team_a, team_b) >= (
                1 - self._team_a_advance_probability(team_a, team_b)
            )
            return (
                MatchResult(team_a_goals=1, team_b_goals=0)
                if favorite_is_a
                else MatchResult(team_a_goals=0, team_b_goals=1)
            )

        outcome = max(probabilities, key=probabilities.get)
        margin = _favorite_margin(
            abs(
                _model_rating(self.base_model, team_a)
                - _model_rating(self.base_model, team_b)
            )
        )

        if outcome == "draw":
            return MatchResult(team_a_goals=1, team_b_goals=1)
        if outcome == "team_a_win":
            return MatchResult(team_a_goals=1 + margin, team_b_goals=1)
        return MatchResult(team_a_goals=1, team_b_goals=1 + margin)

    def _team_a_advance_probability(self, team_a: Team, team_b: Team) -> float:
        probabilities = self.predict_probabilities(team_a, team_b)
        rating_gap = self.rating_for(team_a) - self.rating_for(team_b)
        team_a_tiebreak = 1 / (1 + 10 ** (-rating_gap / 400))
        return probabilities["team_a_win"] + probabilities["draw"] * team_a_tiebreak


def _favorite_margin(rating_gap: float) -> int:
    if rating_gap >= 450:
        return 3
    if rating_gap >= 200:
        return 2
    return 1


def _project_favorite_group_stage(
    config: TournamentConfig,
    match_model: MatchModel,
) -> GroupStageResult:
    """Create a deterministic projected group stage from expected scorelines."""
    teams_by_id = {team.id: team for team in config.teams}
    group_matches: list[Match] = []

    for match in config.matches:
        if match.stage != "group":
            continue
        if match.result is not None and match.result.played:
            group_matches.append(match)
            continue

        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        result = _projected_match_result(match_model, team_a, team_b)
        group_matches.append(match.model_copy(update={"result": result}))

    group_tables = {
        group.id: calculate_group_table(group, teams_by_id, group_matches)
        for group in sorted(config.groups, key=lambda item: item.id)
    }

    top_two_qualifiers = [
        row.team_id
        for group_id in sorted(group_tables)
        for row in group_tables[group_id][:2]
    ]
    third_place_rankings = rank_third_place_teams(group_tables)
    third_place_qualifiers = [
        row.team_id
        for row in get_best_third_place_qualifiers(group_tables, count=8)
    ]

    return GroupStageResult(
        simulated_matches=group_matches,
        group_tables=group_tables,
        top_two_qualifiers=top_two_qualifiers,
        third_place_rankings=third_place_rankings,
        third_place_qualifiers=third_place_qualifiers,
        qualified_team_ids=top_two_qualifiers + third_place_qualifiers,
    )


def _hybrid_group_stage_from_bank(
    config: TournamentConfig,
    match_model: MatchModel,
    *,
    modal_qualified_team_ids: list[str],
) -> GroupStageResult:
    """Use actual standings for finished groups and modal qualifiers elsewhere."""
    teams_by_id = {team.id: team for team in config.teams}
    completed_groups = _completed_group_ids(config)
    group_matches: list[Match] = []

    for match in config.matches:
        if match.stage != "group":
            continue
        if match.result is not None and match.result.played:
            group_matches.append(match)
            continue

        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        result = _projected_match_result(match_model, team_a, team_b)
        group_matches.append(match.model_copy(update={"result": result}))

    group_tables = {
        group.id: calculate_group_table(group, teams_by_id, group_matches)
        for group in sorted(config.groups, key=lambda item: item.id)
    }

    top_two_qualifiers: list[str] = []
    for group_index, group in enumerate(sorted(config.groups, key=lambda item: item.id)):
        if group.id in completed_groups:
            rows = group_tables[group.id]
            top_two_qualifiers.extend([rows[0].team_id, rows[1].team_id])
        else:
            top_two_qualifiers.extend(
                [
                    modal_qualified_team_ids[group_index * 2],
                    modal_qualified_team_ids[group_index * 2 + 1],
                ]
            )

    third_place_rankings = rank_third_place_teams(group_tables)
    third_place_qualifiers = [
        row.team_id
        for row in get_best_third_place_qualifiers(group_tables, count=8)
    ]

    return GroupStageResult(
        simulated_matches=group_matches,
        group_tables=group_tables,
        top_two_qualifiers=top_two_qualifiers,
        third_place_rankings=third_place_rankings,
        third_place_qualifiers=third_place_qualifiers,
        qualified_team_ids=top_two_qualifiers + third_place_qualifiers,
    )


def _modal_group_stage_from_bank(
    bank: dict[str, object],
    config: TournamentConfig,
    match_model: MatchModel,
    *,
    qualified_team_ids: list[str],
) -> GroupStageResult:
    """Create projected group tables aligned with modal bank qualification."""
    teams_by_id = {team.id: team for team in config.teams}
    team_ids: list[str] = bank["team_ids"]  # type: ignore[assignment]
    points: np.ndarray = bank["points"]  # type: ignore[assignment]
    group_matches: list[Match] = []

    for match in config.matches:
        if match.stage != "group":
            continue
        if match.result is not None and match.result.played:
            group_matches.append(match)
            continue

        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        result = _projected_match_result(match_model, team_a, team_b)
        group_matches.append(match.model_copy(update={"result": result}))

    group_tables = {
        group.id: calculate_group_table(group, teams_by_id, group_matches)
        for group in sorted(config.groups, key=lambda item: item.id)
    }

    for group in sorted(config.groups, key=lambda item: item.id):
        rows = list(group_tables[group.id])
        group_team_ids = [team.id for team in config.teams if team.group_id == group.id]
        rows.sort(
            key=lambda row: (
                row.team_id in qualified_team_ids,
                float(np.mean(points[:, team_ids.index(row.team_id)])),
                teams_by_id[row.team_id].rating,
                row.team_id,
            ),
            reverse=True,
        )
        group_tables[group.id] = rows

    top_two_qualifiers = [
        row.team_id
        for group_id in sorted(group_tables)
        for row in group_tables[group_id][:2]
    ]
    third_place_rankings = rank_third_place_teams(group_tables)
    third_place_qualifiers = [
        row.team_id
        for row in get_best_third_place_qualifiers(group_tables, count=8)
    ]
    derived_qualified = top_two_qualifiers + third_place_qualifiers
    if derived_qualified != qualified_team_ids:
        group_tables = _force_modal_group_tables(
            config,
            teams_by_id,
            group_matches,
            qualified_team_ids=qualified_team_ids,
        )
        top_two_qualifiers = qualified_team_ids[:24]
        third_place_qualifiers = qualified_team_ids[24:]
        third_place_rankings = rank_third_place_teams(group_tables)

    return GroupStageResult(
        simulated_matches=group_matches,
        group_tables=group_tables,
        top_two_qualifiers=top_two_qualifiers,
        third_place_rankings=third_place_rankings,
        third_place_qualifiers=third_place_qualifiers,
        qualified_team_ids=qualified_team_ids,
    )


def _force_modal_group_tables(
    config: TournamentConfig,
    teams_by_id: dict[str, Team],
    group_matches: list[Match],
    *,
    qualified_team_ids: list[str],
) -> dict[str, list]:
    """Reorder group tables so modal qualifiers appear in the top two / third slots."""
    group_tables = {
        group.id: calculate_group_table(group, teams_by_id, group_matches)
        for group in sorted(config.groups, key=lambda item: item.id)
    }
    rows_by_team = {
        row.team_id: row
        for rows in group_tables.values()
        for row in rows
    }

    forced_tables: dict[str, list] = {}
    for group_index, group_id in enumerate(sorted(group_tables)):
        winner_id = qualified_team_ids[group_index * 2]
        runner_up_id = qualified_team_ids[group_index * 2 + 1]
        remaining = [
            row
            for row in group_tables[group_id]
            if row.team_id not in {winner_id, runner_up_id}
        ]
        forced_tables[group_id] = [
            rows_by_team[winner_id],
            rows_by_team[runner_up_id],
            *remaining,
        ]

    return forced_tables


def _projected_match_result(
    match_model: MatchModel,
    team_a: Team,
    team_b: Team,
) -> MatchResult:
    projected_result = getattr(match_model, "projected_result", None)
    if callable(projected_result):
        return projected_result(team_a, team_b)

    probabilities = match_model.predict_probabilities(team_a, team_b)
    outcome = max(probabilities, key=probabilities.get)
    if outcome == "draw":
        return MatchResult(team_a_goals=1, team_b_goals=1)
    if outcome == "team_a_win":
        return MatchResult(team_a_goals=2, team_b_goals=1)
    return MatchResult(team_a_goals=1, team_b_goals=2)


def _model_rating(match_model, team: Team) -> float:
    rating_for = getattr(match_model, "rating_for", None)
    if callable(rating_for):
        return float(rating_for(team))

    return _base_model_rating(match_model, team)


def _base_model_rating(match_model, team: Team) -> float:
    base_model = getattr(match_model, "base_model", None)
    base_rating_for = getattr(base_model, "rating_for", None)
    if callable(base_rating_for):
        return float(base_rating_for(team))

    rating_for = getattr(match_model, "rating_for", None)
    if callable(rating_for):
        return float(rating_for(team))

    return team.rating

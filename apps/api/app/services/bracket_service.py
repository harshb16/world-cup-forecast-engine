"""Bracket trace service for interactive tournament reveals."""

import numpy as np

from app.models.domain import Match, MatchResult, Team
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
from app.services.simulation_service import apply_result_overrides, create_match_model
from app.simulation.group_stage import simulate_group_stage
from app.simulation.knockout import simulate_knockout
from app.simulation.match_models import MatchModel


def run_bracket_simulation(
    request: BracketSimulateRequest,
    data_mode: str,
) -> BracketSimulationResponse:
    """Run one tournament trace for client-side bracket reveal."""
    base_config = load_tournament(data_mode)
    config = apply_result_overrides(base_config, request.result_overrides)
    teams_by_id = {team.id: team for team in config.teams}
    base_match_model = create_match_model(request.model_type)
    match_model = (
        _MostLikelyMatchModel(base_match_model)
        if request.simulation_mode == "favorite"
        else base_match_model
    )
    rng = np.random.default_rng(request.seed)

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
                _to_bracket_match(match, teams_by_id, match_model, index)
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
) -> BracketMatchResponse:
    team_a = teams_by_id[match.team_a_id]
    team_b = teams_by_id[match.team_b_id]
    probabilities = match_model.predict_probabilities(team_a, team_b)
    team_a_tiebreak = 1 / (1 + 10 ** (-(team_a.rating - team_b.rating) / 400))
    team_a_advance = probabilities["team_a_win"] + probabilities["draw"] * team_a_tiebreak
    team_b_advance = probabilities["team_b_win"] + probabilities["draw"] * (1 - team_a_tiebreak)

    if match.result is None or match.winner_team_id is None:
        raise ValueError("bracket trace match must include result and winner")

    return BracketMatchResponse(
        id=match.id,
        stage=match.stage,
        match_number=match_number,
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
    )


def _to_bracket_team(team: Team) -> BracketTeamResponse:
    return BracketTeamResponse(
        team_id=team.id,
        team_name=team.name,
        group_id=team.group_id,
        rating=team.rating,
    )


class _MostLikelyMatchModel:
    """Deterministic wrapper that chooses the most likely match outcome."""

    def __init__(self, base_model: MatchModel) -> None:
        self.base_model = base_model

    def predict_probabilities(self, team_a: Team, team_b: Team) -> dict[str, float]:
        return self.base_model.predict_probabilities(team_a, team_b)

    def simulate_result(
        self,
        team_a: Team,
        team_b: Team,
        rng: np.random.Generator,
    ) -> MatchResult:
        probabilities = self.predict_probabilities(team_a, team_b)
        outcome = max(probabilities, key=probabilities.get)
        margin = _favorite_margin(abs(team_a.rating - team_b.rating))

        if outcome == "draw":
            return MatchResult(team_a_goals=1, team_b_goals=1)
        if outcome == "team_a_win":
            return MatchResult(team_a_goals=1 + margin, team_b_goals=1)
        return MatchResult(team_a_goals=1, team_b_goals=1 + margin)


def _favorite_margin(rating_gap: float) -> int:
    if rating_gap >= 450:
        return 3
    if rating_gap >= 200:
        return 2
    return 1

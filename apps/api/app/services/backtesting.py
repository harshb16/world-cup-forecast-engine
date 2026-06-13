"""Baseline backtesting metrics for completed fixtures."""

import math
from typing import Literal

from app.core.config import get_data_mode
from app.models.domain import Match, MatchResult, Team
from app.models.schemas import BacktestingResponse
from app.services.data_loader import load_tournament
from app.services.simulation_service import create_match_model

Outcome = Literal["team_a_win", "draw", "team_b_win"]


def calculate_backtesting_metrics(
    model_type: Literal["elo", "poisson"] = "poisson",
    data_mode: str | None = None,
) -> BacktestingResponse:
    """Score model probabilities against completed group-stage fixtures."""
    mode = data_mode or get_data_mode()
    tournament = load_tournament(mode)
    teams_by_id = {team.id: team for team in tournament.teams}
    completed_matches = [
        match
        for match in tournament.matches
        if match.result is not None and match.result.played
    ]

    if not completed_matches:
        return BacktestingResponse(
            model_type=model_type,
            data_mode=mode,
            sample_size=0,
            accuracy=None,
            brier_score=None,
            log_loss=None,
            limitations=[
                "No completed fixtures are available in this data mode.",
                "Backtesting will become meaningful after real results are ingested.",
            ],
        )

    match_model = create_match_model(model_type)
    exact_predictions = 0
    brier_total = 0.0
    log_loss_total = 0.0

    for match in completed_matches:
        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        probabilities = match_model.predict_probabilities(team_a, team_b)
        actual = _actual_outcome(match.result)
        predicted = max(probabilities, key=probabilities.get)

        if predicted == actual:
            exact_predictions += 1

        brier_total += sum(
            (probabilities[outcome] - (1.0 if outcome == actual else 0.0)) ** 2
            for outcome in ["team_a_win", "draw", "team_b_win"]
        )
        log_loss_total += -math.log(max(probabilities[actual], 1e-15))

    sample_size = len(completed_matches)
    return BacktestingResponse(
        model_type=model_type,
        data_mode=mode,
        sample_size=sample_size,
        accuracy=exact_predictions / sample_size,
        brier_score=brier_total / sample_size,
        log_loss=log_loss_total / sample_size,
        limitations=[
            "Metric sample is small until more completed fixtures are ingested.",
            "This evaluates baseline probability quality only; no model training happens here.",
            "Current fixtures are group-stage only, so knockout behavior is not backtested yet.",
        ],
    )


def _actual_outcome(result: MatchResult) -> Outcome:
    if result.team_a_goals > result.team_b_goals:
        return "team_a_win"
    if result.team_b_goals > result.team_a_goals:
        return "team_b_win"
    return "draw"

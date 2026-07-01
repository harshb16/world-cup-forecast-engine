"""Current-tournament model scoring against completed fixtures."""

import math
from typing import Literal

from app.core.config import get_data_mode
from app.models.domain import MatchResult, Team
from app.models.schemas import (
    CalibrationBinResponse,
    CurrentTournamentMatchScoreResponse,
    CurrentTournamentScoringResponse,
    ModelType,
)
from app.services.data_loader import load_tournament
from app.services.simulation_service import create_match_model

Outcome = Literal["team_a_win", "draw", "team_b_win"]
OUTCOMES: list[Outcome] = ["team_a_win", "draw", "team_b_win"]
NUM_CALIBRATION_BINS = 10


def calculate_current_tournament_scores(
    model_type: ModelType = "poisson",
    data_mode: str | None = None,
) -> CurrentTournamentScoringResponse:
    """Score model probabilities against completed tournament fixtures."""
    mode = data_mode or get_data_mode()
    tournament = load_tournament(mode)
    teams_by_id = {team.id: team for team in tournament.teams}
    completed_matches = [
        match
        for match in tournament.matches
        if match.result is not None and match.result.played
    ]

    if not completed_matches:
        return CurrentTournamentScoringResponse(
            model_type=model_type,
            data_mode=mode,
            sample_size=0,
            accuracy=None,
            brier_score=None,
            log_loss=None,
            limitations=[
                "No completed fixtures are available in this data mode.",
                "Historical out-of-sample backtesting is not provided by this endpoint.",
            ],
        )

    match_model = create_match_model(model_type, mode)
    exact_predictions = 0
    brier_total = 0.0
    log_loss_total = 0.0
    per_match_details: list[CurrentTournamentMatchScoreResponse] = []
    bin_counts = [0 for _ in range(NUM_CALIBRATION_BINS)]
    bin_hits = [0 for _ in range(NUM_CALIBRATION_BINS)]

    for match in completed_matches:
        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        stage = None if match.stage == "group" else "knockout"
        probabilities = _predict_probabilities(match_model, team_a, team_b, stage)
        actual = _actual_outcome(match.result, match.winner_team_id)
        predicted = max(probabilities, key=probabilities.get)
        confidence = probabilities[predicted]

        if predicted == actual:
            exact_predictions += 1

        brier_total += sum(
            (probabilities[outcome] - (1.0 if outcome == actual else 0.0)) ** 2
            for outcome in OUTCOMES
        )
        log_loss_total += -math.log(max(probabilities[actual], 1e-15))

        per_match_details.append(
            CurrentTournamentMatchScoreResponse(
                match_id=match.id,
                predicted_outcome=predicted,
                actual_outcome=actual,
                confidence=confidence,
            )
        )

        for outcome in OUTCOMES:
            probability = probabilities[outcome]
            bin_index = min(int(probability * NUM_CALIBRATION_BINS), NUM_CALIBRATION_BINS - 1)
            bin_counts[bin_index] += 1
            if outcome == actual:
                bin_hits[bin_index] += 1

    calibration_bins = [
        CalibrationBinResponse(
            predicted_midpoint=(index + 0.5) / NUM_CALIBRATION_BINS,
            actual_frequency=bin_hits[index] / bin_counts[index]
            if bin_counts[index]
            else 0.0,
            count=bin_counts[index],
        )
        for index in range(NUM_CALIBRATION_BINS)
    ]

    sample_size = len(completed_matches)
    return CurrentTournamentScoringResponse(
        model_type=model_type,
        data_mode=mode,
        sample_size=sample_size,
        accuracy=exact_predictions / sample_size,
        brier_score=brier_total / sample_size,
        log_loss=log_loss_total / sample_size,
        calibration_bins=calibration_bins,
        per_match_details=per_match_details,
        limitations=[
            "Metric sample is small until more completed fixtures are ingested.",
            "This scores the current model against matches from this tournament only.",
            "This is not a historical out-of-sample backtest and must not be read as proof of model superiority.",
            "Penalty shootouts are scored using regulation/extra-time W/D/L; the decisive penalty winner is noted separately in match metadata.",
        ],
    )


def _predict_probabilities(
    match_model,
    team_a: Team,
    team_b: Team,
    stage: str | None,
) -> dict[str, float]:
    predict = getattr(match_model, "predict_probabilities", None)
    if predict is None:
        raise ValueError("match model must expose predict_probabilities")
    try:
        return predict(team_a, team_b, stage=stage)
    except TypeError:
        return predict(team_a, team_b)


def _actual_outcome(result: MatchResult, winner_team_id: str | None) -> Outcome:
    if result.decided_by_penalties:
        if result.team_a_goals > result.team_b_goals:
            return "team_a_win"
        if result.team_b_goals > result.team_a_goals:
            return "team_b_win"
        return "draw"
    if result.team_a_goals > result.team_b_goals:
        return "team_a_win"
    if result.team_b_goals > result.team_a_goals:
        return "team_b_win"
    return "draw"

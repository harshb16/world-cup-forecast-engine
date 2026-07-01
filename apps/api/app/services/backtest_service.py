"""Historical tournament backtesting against fixed past World Cup data."""

import json
import math
from pathlib import Path
from typing import Literal

from app.models.domain import Match, Team, TournamentConfig
from app.models.schemas import (
    CalibrationBinResponse,
    CurrentTournamentMatchScoreResponse,
    HistoricalBacktestResponse,
    ModelType,
)
from app.services.current_tournament_scoring import (
    OUTCOMES,
    NUM_CALIBRATION_BINS,
    _actual_outcome,
    _predict_probabilities,
)
from app.services.simulation_service import create_match_model

REPO_ROOT = Path(__file__).resolve().parents[4]
HISTORICAL_ROOT = REPO_ROOT / "data" / "historical"
SupportedTournament = Literal["2022"]


def calculate_historical_backtest(
    tournament: SupportedTournament = "2022",
    model_type: ModelType = "poisson",
) -> HistoricalBacktestResponse:
    """Score a model against a fixed historical World Cup dataset."""
    config = _load_historical_tournament(tournament)
    teams_by_id = {team.id: team for team in config.teams}
    completed_matches = [
        match
        for match in config.matches
        if match.result is not None and match.result.played
    ]

    if not completed_matches:
        return HistoricalBacktestResponse(
            tournament=tournament,
            model_type=model_type,
            sample_size=0,
            accuracy=None,
            brier_score=None,
            log_loss=None,
            limitations=["Historical dataset has no completed matches."],
        )

    match_model = create_match_model(model_type, "sample")
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
    metadata = _load_historical_metadata(tournament)
    return HistoricalBacktestResponse(
        tournament=tournament,
        model_type=model_type,
        sample_size=sample_size,
        accuracy=exact_predictions / sample_size,
        brier_score=brier_total / sample_size,
        log_loss=log_loss_total / sample_size,
        calibration_bins=calibration_bins,
        per_match_details=per_match_details,
        limitations=[
            "This is a genuine out-of-sample historical evaluation on a fixed past tournament.",
            metadata.get(
                "coverage_note",
                "Historical dataset coverage may be partial during bootstrap.",
            ),
            "Team ratings are mapped from tournament-era strength proxies, not pre-tournament snapshots.",
        ],
    )


def _load_historical_tournament(tournament: SupportedTournament) -> TournamentConfig:
    directory = HISTORICAL_ROOT / f"wc{tournament}"
    teams = [Team.model_validate(item) for item in _read_json(directory / "teams.json")]
    groups = _read_json(directory / "groups.json")
    from app.models.domain import Group

    return TournamentConfig(
        teams=teams,
        groups=[Group.model_validate(item) for item in groups],
        matches=[Match.model_validate(item) for item in _read_json(directory / "fixtures.json")],
    )


def _load_historical_metadata(tournament: SupportedTournament) -> dict[str, object]:
    path = HISTORICAL_ROOT / f"wc{tournament}" / "metadata.json"
    if not path.exists():
        return {}
    payload = _read_json(path)
    return payload if isinstance(payload, dict) else {}


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))

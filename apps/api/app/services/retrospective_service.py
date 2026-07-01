"""Tournament retrospective built from probability history and scoring."""

from __future__ import annotations

from app.core.config import DEFAULT_MODEL_TYPE, get_data_mode
from app.models.schemas import (
    ModelType,
    RetrospectiveChampionArcPointResponse,
    RetrospectiveMatchInsightResponse,
    RetrospectiveResponse,
)
from app.services.current_tournament_scoring import calculate_current_tournament_scores
from app.services.data_loader import load_tournament
from app.services.probability_timeline_service import build_probability_timeline


def calculate_retrospective(
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    data_mode: str | None = None,
) -> RetrospectiveResponse:
    """Build retrospective summary for the active tournament dataset."""
    mode = data_mode or get_data_mode()
    tournament = load_tournament(mode)
    teams_by_id = {team.id: team for team in tournament.teams}
    scoring = calculate_current_tournament_scores(model_type, mode)
    champion_team_id, champion_team_name = _tournament_champion(tournament, teams_by_id)

    timeline = build_probability_timeline(mode, model_type=model_type)
    top_team_ids = _top_team_ids_from_timeline(timeline.snapshots)
    champion_arc = [
        RetrospectiveChampionArcPointResponse(
            label=snapshot.label,
            milestone_id=snapshot.milestone_id,
            champion_probabilities={
                team_id: snapshot.champion_probabilities.get(team_id, 0.0)
                for team_id in top_team_ids
            },
        )
        for snapshot in timeline.snapshots
    ]

    pre_tournament_probability = None
    if champion_team_id and timeline.snapshots:
        first_snapshot = timeline.snapshots[0]
        pre_tournament_probability = first_snapshot.champion_probabilities.get(
            champion_team_id
        )

    matches_by_id = {match.id: match for match in tournament.matches}
    insights: list[RetrospectiveMatchInsightResponse] = []
    for detail in scoring.per_match_details:
        match = matches_by_id.get(detail.match_id)
        if match is None:
            continue
        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        insights.append(
            RetrospectiveMatchInsightResponse(
                match_id=detail.match_id,
                stage=match.stage,
                team_a_name=team_a.name,
                team_b_name=team_b.name,
                predicted_outcome=detail.predicted_outcome,
                actual_outcome=detail.actual_outcome,
                confidence=detail.confidence,
                correct=detail.predicted_outcome == detail.actual_outcome,
            )
        )

    hits = sorted(
        [item for item in insights if item.correct],
        key=lambda item: item.confidence,
        reverse=True,
    )[:5]
    misses = sorted(
        [item for item in insights if not item.correct],
        key=lambda item: item.confidence,
        reverse=True,
    )[:5]

    return RetrospectiveResponse(
        model_type=model_type,
        data_mode=mode,
        champion_team_id=champion_team_id,
        champion_team_name=champion_team_name,
        pre_tournament_champion_probability=pre_tournament_probability,
        champion_arc=champion_arc,
        top_hits=hits,
        top_misses=misses,
        scoring=scoring,
        limitations=[
            "Retrospective uses the current processed dataset and model parameters.",
            "Pre-tournament champion probability comes from the earliest stored milestone.",
            "This is descriptive scoring on observed results, not out-of-sample proof.",
        ],
    )


def _tournament_champion(tournament, teams_by_id: dict) -> tuple[str | None, str | None]:
    final_matches = [
        match
        for match in tournament.matches
        if match.stage == "Final"
        and match.result is not None
        and match.result.played
        and match.winner_team_id
    ]
    if not final_matches:
        return None, None
    champion_id = final_matches[0].winner_team_id
    if champion_id is None:
        return None, None
    champion = teams_by_id.get(champion_id)
    return champion_id, champion.name if champion else champion_id


def _top_team_ids_from_timeline(snapshots) -> list[str]:
    if not snapshots:
        return []
    latest = snapshots[-1].champion_probabilities
    return [
        team_id
        for team_id, _ in sorted(latest.items(), key=lambda item: item[1], reverse=True)[:5]
    ]

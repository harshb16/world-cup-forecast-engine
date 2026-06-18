"""Analytics services for upset radar, group chaos, and model comparison."""

import math

from app.models.schemas import (
    BracketSimulateRequest,
    GroupChaosResponse,
    GroupChaosScoreResponse,
    ModelComparisonDeltaResponse,
    ModelComparisonResponse,
    ModelType,
    SimulateRequest,
    UpsetFixtureResponse,
    UpsetRadarResponse,
)
from app.services.bracket_service import run_bracket_simulation
from app.services.data_loader import load_tournament
from app.services.simulation_service import create_match_model, run_simulation


STAGE_IMPORTANCE: dict[str, float] = {
    "group": 1.0,
    "Round of 32": 1.2,
    "Round of 16": 1.4,
    "Quarter-finals": 1.6,
    "Semi-finals": 1.8,
    "Final": 2.0,
}

RISK_LABELS = (
    (0.35, "High"),
    (0.22, "Elevated"),
    (0.12, "Moderate"),
)


def calculate_upset_radar(
    data_mode: str,
    model_type: ModelType = "oracle_v2",
    limit: int = 12,
) -> UpsetRadarResponse:
    """Rank fixtures by upset risk using advance probability gaps."""
    config = load_tournament(data_mode)
    teams_by_id = {team.id: team for team in config.teams}
    match_model = create_match_model(model_type, data_mode)
    upsets: list[UpsetFixtureResponse] = []

    for match in config.matches:
        if match.stage != "group":
            continue
        if match.result is not None and match.result.played:
            continue

        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        probabilities = match_model.predict_probabilities(team_a, team_b)
        favorite_id, underdog_id, favorite_prob, underdog_prob = _favorite_underdog(
            team_a,
            team_b,
            probabilities,
        )
        gap = favorite_prob - underdog_prob
        stage_weight = STAGE_IMPORTANCE["group"]
        upset_score = underdog_prob * (1 - gap) * stage_weight
        upsets.append(
            UpsetFixtureResponse(
                match_id=match.id,
                stage=match.stage,
                group_id=match.group_id,
                team_a_id=team_a.id,
                team_a_name=team_a.name,
                team_b_id=team_b.id,
                team_b_name=team_b.name,
                favorite_team_id=favorite_id,
                underdog_team_id=underdog_id,
                favorite_advance_probability=favorite_prob,
                underdog_advance_probability=underdog_prob,
                advance_probability_gap=gap,
                upset_score=upset_score,
                risk_label=_risk_label(upset_score),
                stage_importance=stage_weight,
                reasons=_upset_reasons(gap, underdog_prob, match.stage),
            )
        )

    bracket = run_bracket_simulation(
        BracketSimulateRequest(model_type=model_type, simulation_mode="favorite", seed=42),
        data_mode,
    )
    for stage, matches in bracket.rounds.items():
        stage_weight = STAGE_IMPORTANCE.get(stage, 1.0)
        for match in matches:
            favorite_advance = max(
                match.probabilities.team_a_advance,
                match.probabilities.team_b_advance,
            )
            underdog_advance = min(
                match.probabilities.team_a_advance,
                match.probabilities.team_b_advance,
            )
            gap = favorite_advance - underdog_advance
            upset_score = underdog_advance * (1 - gap) * stage_weight
            favorite_id = (
                match.team_a.team_id
                if match.probabilities.team_a_advance >= match.probabilities.team_b_advance
                else match.team_b.team_id
            )
            underdog_id = (
                match.team_b.team_id
                if favorite_id == match.team_a.team_id
                else match.team_a.team_id
            )
            upsets.append(
                UpsetFixtureResponse(
                    match_id=match.id,
                    stage=stage,
                    group_id=None,
                    team_a_id=match.team_a.team_id,
                    team_a_name=match.team_a.team_name,
                    team_b_id=match.team_b.team_id,
                    team_b_name=match.team_b.team_name,
                    favorite_team_id=favorite_id,
                    underdog_team_id=underdog_id,
                    favorite_advance_probability=favorite_advance,
                    underdog_advance_probability=underdog_advance,
                    advance_probability_gap=gap,
                    upset_score=upset_score,
                    risk_label=_risk_label(upset_score),
                    stage_importance=stage_weight,
                    reasons=_upset_reasons(gap, underdog_advance, stage),
                )
            )

    upsets.sort(key=lambda item: item.upset_score, reverse=True)
    return UpsetRadarResponse(
        model_type=model_type,
        data_mode=data_mode,
        fixtures=upsets[:limit],
    )


def calculate_group_chaos(
    data_mode: str,
    model_type: ModelType = "oracle_v2",
    n_simulations: int = 500,
    seed: int = 42,
) -> GroupChaosResponse:
    """Compute group chaos scores from simulation output."""
    summary = run_simulation(
        SimulateRequest(
            n_simulations=n_simulations,
            model_type=model_type,
            seed=seed,
        ),
        data_mode,
    )
    config = load_tournament(data_mode)
    teams_by_group: dict[str, list] = {}
    for team in summary.teams:
        teams_by_group.setdefault(team.group_id, []).append(team)

    groups: list[GroupChaosScoreResponse] = []
    for group in config.groups:
        group_teams = teams_by_group.get(group.id, [])
        if not group_teams:
            continue

        qual_probs = [team.group_qualification_probability for team in group_teams]
        entropy = _normalized_entropy(qual_probs)
        points = [team.average_points for team in group_teams]
        point_spread = max(points) - min(points) if points else 0.0
        spread_factor = min(point_spread / 6.0, 1.0)
        chaos_score = 0.7 * entropy + 0.3 * spread_factor
        key_match = _key_swing_match(config, group.id, model_type, data_mode)

        groups.append(
            GroupChaosScoreResponse(
                group_id=group.id,
                group_name=group.name,
                chaos_score=chaos_score,
                chaos_label=_chaos_label(chaos_score),
                qualification_entropy=entropy,
                average_point_spread=point_spread,
                key_swing_match_id=key_match["match_id"] if key_match else None,
                key_swing_match_label=key_match["label"] if key_match else None,
                teams=[
                    {
                        "team_id": team.team_id,
                        "team_name": team.team_name,
                        "group_qualification_probability": team.group_qualification_probability,
                        "top_two_probability": team.top_two_probability,
                        "average_points": team.average_points,
                    }
                    for team in group_teams
                ],
            )
        )

    groups.sort(key=lambda item: item.chaos_score, reverse=True)
    return GroupChaosResponse(
        model_type=model_type,
        data_mode=data_mode,
        n_simulations=n_simulations,
        groups=groups,
    )


def calculate_model_comparison(
    data_mode: str,
    n_simulations: int = 300,
    seed: int = 42,
    baseline_model: ModelType = "oracle_v2",
) -> ModelComparisonResponse:
    """Compare champion and top-four probabilities across model types."""
    model_types: list[ModelType] = ["elo", "poisson", "calibrated_elo", "oracle_v2"]
    summaries = {
        model_type: run_simulation(
            SimulateRequest(
                n_simulations=n_simulations,
                model_type=model_type,
                seed=seed,
            ),
            data_mode,
        )
        for model_type in model_types
    }
    baseline = summaries[baseline_model]
    baseline_champion = baseline.champion_probabilities
    top_four_ids = sorted(
        baseline_champion,
        key=baseline_champion.get,
        reverse=True,
    )[:4]

    deltas: list[ModelComparisonDeltaResponse] = []
    for model_type in model_types:
        if model_type == baseline_model:
            continue
        comparison = summaries[model_type]
        champion_deltas = {
            team_id: comparison.champion_probabilities[team_id]
            - baseline_champion[team_id]
            for team_id in baseline_champion
        }
        top_four_deltas = {
            team_id: champion_deltas[team_id]
            for team_id in top_four_ids
        }
        deltas.append(
            ModelComparisonDeltaResponse(
                model_type=model_type,
                baseline_model=baseline_model,
                champion_probability_deltas=champion_deltas,
                top_four_probability_deltas=top_four_deltas,
                largest_positive_delta_team_id=max(
                    champion_deltas,
                    key=champion_deltas.get,
                ),
                largest_negative_delta_team_id=min(
                    champion_deltas,
                    key=champion_deltas.get,
                ),
            )
        )

    return ModelComparisonResponse(
        data_mode=data_mode,
        n_simulations=n_simulations,
        seed=seed,
        baseline_model=baseline_model,
        champion_probabilities={
            model_type: summaries[model_type].champion_probabilities
            for model_type in model_types
        },
        top_four_team_ids=top_four_ids,
        model_deltas=deltas,
    )


def _favorite_underdog(
    team_a,
    team_b,
    probabilities: dict[str, float],
) -> tuple[str, str, float, float]:
    team_a_strength = probabilities["team_a_win"] + 0.5 * probabilities["draw"]
    team_b_strength = probabilities["team_b_win"] + 0.5 * probabilities["draw"]
    if team_a_strength >= team_b_strength:
        return team_a.id, team_b.id, team_a_strength, team_b_strength
    return team_b.id, team_a.id, team_b_strength, team_a_strength


def _risk_label(score: float) -> str:
    for threshold, label in RISK_LABELS:
        if score >= threshold:
            return label
    return "Low"


def _upset_reasons(gap: float, underdog_probability: float, stage: str) -> list[str]:
    reasons: list[str] = []
    if gap < 0.12:
        reasons.append("Advance probabilities are nearly even.")
    elif gap < 0.22:
        reasons.append("Favorite edge is thin for this stage.")
    if underdog_probability >= 0.35:
        reasons.append("Underdog still has a credible path to advance.")
    if stage in {"Semi-finals", "Final"}:
        reasons.append("Late-stage knockout variance is high-impact.")
    if not reasons:
        reasons.append("Model sees a non-trivial upset path despite favorite edge.")
    return reasons


def _normalized_entropy(probabilities: list[float]) -> float:
    total = sum(probabilities)
    if total <= 0 or len(probabilities) <= 1:
        return 0.0
    entropy = sum(
        -(probability / total) * math.log(probability / total)
        for probability in probabilities
        if probability > 0
    )
    return entropy / math.log(len(probabilities))


def _chaos_label(score: float) -> str:
    if score >= 0.78:
        return "High"
    if score >= 0.62:
        return "Medium"
    return "Low"


def _key_swing_match(
    config,
    group_id: str,
    model_type: ModelType,
    data_mode: str,
) -> dict[str, str] | None:
    teams_by_id = {team.id: team for team in config.teams}
    match_model = create_match_model(model_type, data_mode)
    best_match: dict[str, str] | None = None
    best_gap = float("inf")

    for match in config.matches:
        if match.group_id != group_id:
            continue
        if match.result is not None and match.result.played:
            continue
        team_a = teams_by_id[match.team_a_id]
        team_b = teams_by_id[match.team_b_id]
        probabilities = match_model.predict_probabilities(team_a, team_b)
        gap = abs(
            probabilities["team_a_win"] + 0.5 * probabilities["draw"]
            - (probabilities["team_b_win"] + 0.5 * probabilities["draw"])
        )
        if gap < best_gap:
            best_gap = gap
            best_match = {
                "match_id": match.id,
                "label": f"{team_a.name} vs {team_b.name}",
            }

    return best_match

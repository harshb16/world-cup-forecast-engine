"""Probability mover calculations from snapshot history."""

import json
from pathlib import Path

from app.models.schemas import ProbabilityMoverResponse, ProbabilityMoversResponse
from app.services.data_loader import load_tournament

REPO_ROOT = Path(__file__).resolve().parents[4]
PROCESSED_DIR = REPO_ROOT / "data" / "processed"


def calculate_probability_movers(limit: int = 8) -> ProbabilityMoversResponse:
    history_path = PROCESSED_DIR / "probability_history.json"
    if not history_path.exists():
        return ProbabilityMoversResponse(risers=[], fallers=[])
    snapshots = json.loads(history_path.read_text(encoding="utf-8"))
    if len(snapshots) < 2:
        return ProbabilityMoversResponse(risers=[], fallers=[])
    previous, current = snapshots[-2], snapshots[-1]
    teams_by_id = {t.id: t for t in load_tournament("processed").teams}
    deltas = []
    for team_id, current_probability in current.get("champion_probabilities", {}).items():
        team = teams_by_id.get(team_id)
        if team is None:
            continue
        previous_probability = previous.get("champion_probabilities", {}).get(team_id, 0.0)
        deltas.append(
            ProbabilityMoverResponse(
                team_id=team_id,
                team_name=team.name,
                previous_probability=previous_probability,
                current_probability=current_probability,
                delta=current_probability - previous_probability,
            )
        )
    risers = sorted(deltas, key=lambda item: item.delta, reverse=True)[:limit]
    fallers = sorted(deltas, key=lambda item: item.delta)[:limit]
    return ProbabilityMoversResponse(
        risers=risers,
        fallers=fallers,
        previous_timestamp=previous.get("timestamp"),
        current_timestamp=current.get("timestamp"),
    )

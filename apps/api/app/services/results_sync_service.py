"""Atomic operator-managed World Cup result synchronization."""

from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import tempfile
import threading
import unicodedata
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.models.schemas import ForecastSnapshotResponse, SyncJobStage, SyncResponse
from app.services.bracket_materialization_service import (
    materialize_pending_knockout_rounds,
    winners_from_previous_round,
)

from app.services.runtime_store import (
    get_runtime_root,
    publish_data_snapshot,
    resolve_processed_data_directory,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
BOOTSTRAP_PROCESSED_DIR = REPO_ROOT / "data" / "processed"
FIFA_API_URL = (
    "https://api.fifa.com/api/v3/calendar/matches?count=500&idSeason=285023"
)
FOOTBALL_DATA_API_URL = "https://api.football-data.org/v4/competitions/WC/matches"
SYNC_FILES = ("fixtures.json", "results.json", "metadata.json", "data_quality.json")
_SYNC_LOCK = threading.Lock()

TEAM_ALIASES = {
    "bosnia herzegovina": "BIH",
    "cape verde": "CPV",
    "congo dr": "COD",
    "cote divoire": "CIV",
    "czech republic": "CZECHIA",
    "iran": "IRN",
    "korea republic": "KOR",
    "saudi arabia": "SAUDI_ARABIA",
    "south korea": "KOR",
    "turkey": "TURKIYE",
    "united states": "USA",
    "usa": "USA",
}

def _active_processed_dir() -> Path:
    return resolve_processed_data_directory()


FIFA_ABBREVIATIONS = {
    "MEX": "MEXICO",
    "RSA": "RSA",
    "KOR": "KOR",
    "CZE": "CZECHIA",
    "CAN": "CANADA",
    "QAT": "QATAR",
    "BIH": "BIH",
    "SUI": "SWITZERLAND",
    "BRA": "BRAZIL",
    "MAR": "MOROCCO",
    "HAI": "HAITI",
    "SCO": "SCOTLAND",
    "USA": "USA",
    "PAR": "PARAGUAY",
    "AUS": "AUSTRALIA",
    "TUR": "TURKIYE",
    "GER": "GERMANY",
    "CUW": "CURACAO",
    "CIV": "CIV",
    "ECU": "ECUADOR",
    "NED": "NETHERLANDS",
    "JPN": "JAPAN",
    "SWE": "SWEDEN",
    "TUN": "TUNISIA",
    "BEL": "BELGIUM",
    "EGY": "EGYPT",
    "IRN": "IRN",
    "NZL": "NEW_ZEALAND",
    "ESP": "SPAIN",
    "CPV": "CPV",
    "KSA": "SAUDI_ARABIA",
    "URU": "URUGUAY",
    "FRA": "FRANCE",
    "SEN": "SENEGAL",
    "IRQ": "IRAQ",
    "NOR": "NORWAY",
    "ARG": "ARGENTINA",
    "ALG": "ALGERIA",
    "AUT": "AUSTRIA",
    "JOR": "JORDAN",
    "POR": "PORTUGAL",
    "COD": "COD",
    "UZB": "UZBEKISTAN",
    "COL": "COLOMBIA",
    "ENG": "ENGLAND",
    "CRO": "CROATIA",
    "GHA": "GHANA",
    "PAN": "PANAMA",
}


class ResultsSyncError(RuntimeError):
    """Raised when a result refresh cannot be safely published."""


class ResultsConflictError(ResultsSyncError):
    """Raised when a provider contradicts an already-published score."""


def admin_key_is_valid(provided_key: str | None) -> bool:
    """Return whether an operator key matches the configured admin key."""
    configured_key = os.getenv("WCO_ADMIN_SYNC_KEY")
    return bool(
        configured_key
        and provided_key
        and secrets.compare_digest(provided_key, configured_key)
    )


def admin_sync_is_configured() -> bool:
    """Return whether result sync has an operator key configured."""
    return bool(os.getenv("WCO_ADMIN_SYNC_KEY"))


StageReporter = Callable[[SyncJobStage, str | None], None]


def sync_results(on_stage: StageReporter | None = None) -> SyncResponse:
    """Fetch, validate, and publish a complete result snapshot."""

    def report(stage: SyncJobStage, message: str | None = None) -> None:
        if on_stage is not None:
            on_stage(stage, message)

    if not _SYNC_LOCK.acquire(blocking=False):
        return SyncResponse(
            success=False,
            last_updated=_current_last_updated(),
            errors=["A result sync is already running."],
        )

    try:
        report("fetch", "Fetching provider feeds")
        fixtures = _read_json(_active_processed_dir() / "fixtures.json")
        existing_results = _read_json(_active_processed_dir() / "results.json")
        teams = _read_json(_active_processed_dir() / "teams.json")
        provider, provider_matches = _fetch_provider_matches()
        report("normalize", f"Normalizing {provider} payload")
        updated_fixtures, results, changed_count = _merge_fixtures_with_materialization(
            fixtures,
            teams,
            existing_results,
            provider,
            provider_matches,
        )
        report("compare", "Provider scores compared against published results")
        timestamp = datetime.now(tz=UTC).replace(microsecond=0).isoformat()

        with tempfile.TemporaryDirectory(
            prefix=".results-sync-",
            dir=get_runtime_root(),
        ) as temporary_directory:
            staged_dir = Path(temporary_directory) / "processed"
            shutil.copytree(_active_processed_dir(), staged_dir)
            _write_json(staged_dir / "fixtures.json", updated_fixtures)
            _write_json(staged_dir / "results.json", results)
            _stage_metadata(staged_dir, timestamp, provider)
            _stage_data_quality(staged_dir, timestamp, len(results))
            report("validate", "Validating tournament invariants")
            errors = _validate_staged_data(staged_dir)
            if errors:
                raise ResultsSyncError("; ".join(errors))
            report("publish", "Publishing validated data snapshot")
            _publish_files(staged_dir)

        report("forecast", "Generating forecast snapshot")
        forecast = _refresh_forecast_snapshot()
        _append_probability_snapshot(
            timestamp,
            forecast.summary.champion_probabilities,
        )
        report("done", "Sync completed")
        return SyncResponse(
            success=True,
            last_updated=timestamp,
            provider=provider,
            completed_result_count=len(results),
            changed_fixture_count=changed_count,
            errors=[],
        )
    except ResultsConflictError as exc:
        report("compare", str(exc))
        return SyncResponse(
            success=False,
            last_updated=_current_last_updated(),
            errors=[str(exc)],
        )
    except (ResultsSyncError, HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        return SyncResponse(
            success=False,
            last_updated=_current_last_updated(),
            errors=[str(exc)],
        )
    finally:
        _SYNC_LOCK.release()


def _fetch_provider_matches() -> tuple[str, list[dict[str, Any]]]:
    token = os.getenv("FOOTBALL_DATA_API_TOKEN")
    if token:
        try:
            query = urlencode({"season": "2026"})
            payload = _fetch_json(
                f"{FOOTBALL_DATA_API_URL}?{query}",
                headers={"X-Auth-Token": token},
            )
            matches = payload.get("matches")
            if not isinstance(matches, list) or not matches:
                raise ResultsSyncError("football-data.org response missing matches.")
            return "football-data.org", matches
        except (ResultsSyncError, HTTPError, URLError, TimeoutError, ValueError):
            pass

    payload = _fetch_json(FIFA_API_URL)
    matches = payload.get("Results")
    if not isinstance(matches, list):
        raise ResultsSyncError("FIFA fallback response missing Results.")
    return "FIFA API fallback", matches


def _fetch_json(
    url: str,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "WorldCupOracle/1.0",
            **(headers or {}),
        },
    )
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ResultsSyncError(f"Provider returned invalid JSON from {url}.")
    return payload


def _merge_fixtures_with_materialization(
    fixtures: list[dict[str, Any]],
    teams: list[dict[str, Any]],
    existing_results: list[dict[str, Any]],
    provider: str,
    provider_matches: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Materialize knockout fixtures, merge provider results, repeat until stable."""
    changed_total = 0
    current = _append_materialized_knockout_fixtures(fixtures, teams)
    results: list[dict[str, Any]] = []

    for _ in range(8):
        merged, results, changed = _merge_provider_matches(
            current,
            teams,
            existing_results,
            provider,
            provider_matches,
        )
        changed_total += changed
        with_materialized = _append_materialized_knockout_fixtures(merged, teams)
        if len(with_materialized) == len(merged) and changed == 0:
            return with_materialized, results, changed_total
        current = with_materialized

    return current, results, changed_total


def _merge_provider_matches(
    fixtures: list[dict[str, Any]],
    teams: list[dict[str, Any]],
    existing_results: list[dict[str, Any]],
    provider: str,
    provider_matches: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    aliases = {_normalize(team["name"]): team["id"] for team in teams}
    aliases.update(TEAM_ALIASES)
    parsed_matches = (
        _parse_football_data_matches(provider_matches, aliases)
        if provider == "football-data.org"
        else _parse_fifa_matches(provider_matches)
    )
    if not parsed_matches:
        raise ResultsSyncError(f"{provider} returned no recognizable World Cup matches.")
    provider_index = {
        _team_pair(match["team_a_id"], match["team_b_id"]): match
        for match in parsed_matches
    }
    existing_sources = {
        result["match_id"]: result.get("source", "previous published result")
        for result in existing_results
    }
    changed_count = 0
    updated_fixtures: list[dict[str, Any]] = []

    for fixture in fixtures:
        updated = dict(fixture)
        stage = fixture.get("stage", "group")
        incoming = provider_index.get(
            _team_pair(fixture["team_a_id"], fixture["team_b_id"])
        )
        if incoming is None:
            updated_fixtures.append(updated)
            continue

        if stage != "group":
            _validate_knockout_progression(updated, updated_fixtures)

        updated = _apply_match_update(updated, incoming, provider)
        persisted_update = {
            key: value
            for key, value in updated.items()
            if key != "result_source"
        }
        if persisted_update != fixture:
            changed_count += 1
        updated_fixtures.append(updated)

    results = [
        _result_record(fixture, existing_sources)
        for fixture in updated_fixtures
        if fixture.get("status") == "finished"
        and isinstance(fixture.get("result"), dict)
        and fixture["result"].get("played")
    ]
    for fixture in updated_fixtures:
        fixture.pop("result_source", None)
    results.sort(key=lambda row: row["match_id"])
    return updated_fixtures, results, changed_count


def _apply_match_update(
    fixture: dict[str, Any],
    incoming: dict[str, Any],
    provider: str,
) -> dict[str, Any]:
    updated = dict(fixture)
    if incoming.get("kickoff_utc"):
        updated["kickoff_utc"] = incoming["kickoff_utc"]
        updated["kickoff"] = incoming["kickoff_utc"][:10]

    incoming_status = incoming.get("status", "scheduled")
    if incoming_status == "in_play":
        updated["status"] = "in_play"
        score_a = incoming.get("team_a_goals")
        score_b = incoming.get("team_b_goals")
        if score_a is not None and score_b is not None:
            updated["result"] = {
                "played": False,
                "team_a_goals": score_a,
                "team_b_goals": score_b,
            }
        updated["result_source"] = provider
        return updated

    if incoming_status != "finished":
        updated["status"] = incoming_status
        return updated

    updated["status"] = "finished"
    score_a, score_b = _orient_score(fixture, incoming)
    existing = fixture.get("result")
    if isinstance(existing, dict) and existing.get("played"):
        existing_score = (
            existing.get("team_a_goals"),
            existing.get("team_b_goals"),
        )
        if existing_score != (score_a, score_b):
            raise ResultsConflictError(
                f"{provider} conflicts with published score for {fixture['id']}: "
                f"{existing_score[0]}-{existing_score[1]} vs {score_a}-{score_b}."
            )

    result_payload: dict[str, Any] = {
        "played": True,
        "team_a_goals": score_a,
        "team_b_goals": score_b,
    }
    if incoming.get("decided_by_penalties"):
        result_payload["decided_by_penalties"] = True
        pen_a, pen_b = _orient_penalty_score(fixture, incoming)
        result_payload["penalty_team_a_goals"] = pen_a
        result_payload["penalty_team_b_goals"] = pen_b
        updated["winner_team_id"] = (
            fixture["team_a_id"] if pen_a > pen_b else fixture["team_b_id"]
        )
    else:
        updated["winner_team_id"] = (
            fixture["team_a_id"]
            if score_a > score_b
            else fixture["team_b_id"]
            if score_b > score_a
            else None
        )
    updated["result"] = result_payload
    updated["result_source"] = provider
    return updated


def _parse_football_data_matches(
    matches: list[dict[str, Any]],
    aliases: dict[str, str],
) -> list[dict[str, Any]]:
    from app.services.provider_status import football_data_status

    parsed: list[dict[str, Any]] = []
    for match in matches:
        home = match.get("homeTeam") or {}
        away = match.get("awayTeam") or {}
        home_id = _football_data_team_id(home, aliases)
        away_id = _football_data_team_id(away, aliases)
        if home_id is None or away_id is None:
            continue
        full_time = (match.get("score") or {}).get("fullTime") or {}
        extra_time = (match.get("score") or {}).get("extraTime") or {}
        penalties = (match.get("score") or {}).get("penalties") or {}
        status = football_data_status(match.get("status"))
        finished = status == "finished"
        if extra_time.get("home") is not None and extra_time.get("away") is not None:
            home_goals = extra_time.get("home")
            away_goals = extra_time.get("away")
        else:
            home_goals = full_time.get("home")
            away_goals = full_time.get("away")
        if finished and (home_goals is None or away_goals is None):
            continue
        decided_by_penalties = (
            penalties.get("home") is not None and penalties.get("away") is not None
        )
        parsed.append(
            {
                "team_a_id": home_id,
                "team_b_id": away_id,
                "team_a_goals": int(home_goals) if home_goals is not None else None,
                "team_b_goals": int(away_goals) if away_goals is not None else None,
                "kickoff_utc": match.get("utcDate"),
                "status": status,
                "decided_by_penalties": decided_by_penalties,
                "penalty_team_a_goals": int(penalties["home"])
                if decided_by_penalties
                else None,
                "penalty_team_b_goals": int(penalties["away"])
                if decided_by_penalties
                else None,
            }
        )
    return parsed


def _football_data_team_id(
    side: dict[str, Any],
    aliases: dict[str, str],
) -> str | None:
    for key in ("name", "shortName"):
        value = side.get(key)
        if isinstance(value, str) and _normalize(value) in aliases:
            return aliases[_normalize(value)]
    tla = side.get("tla")
    if isinstance(tla, str):
        return FIFA_ABBREVIATIONS.get(tla.upper())
    return None


def _parse_fifa_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from app.services.provider_status import fifa_status

    parsed: list[dict[str, Any]] = []
    for match in matches:
        home = match.get("Home") or {}
        away = match.get("Away") or {}
        home_id = FIFA_ABBREVIATIONS.get(str(home.get("Abbreviation", "")).upper())
        away_id = FIFA_ABBREVIATIONS.get(str(away.get("Abbreviation", "")).upper())
        if home_id is None or away_id is None:
            continue
        status = fifa_status(match.get("MatchStatus"))
        finished = status == "finished"
        home_goals = match.get("HomeTeamScore")
        away_goals = match.get("AwayTeamScore")
        if finished and (home_goals is None or away_goals is None):
            continue
        parsed.append(
            {
                "team_a_id": home_id,
                "team_b_id": away_id,
                "team_a_goals": int(home_goals) if home_goals is not None else None,
                "team_b_goals": int(away_goals) if away_goals is not None else None,
                "kickoff_utc": match.get("KickOffTimeUtc") or match.get("Date"),
                "status": status,
            }
        )
    return parsed


def _orient_penalty_score(
    fixture: dict[str, Any],
    incoming: dict[str, Any],
) -> tuple[int, int]:
    if (
        fixture["team_a_id"] == incoming["team_a_id"]
        and fixture["team_b_id"] == incoming["team_b_id"]
    ):
        return incoming["penalty_team_a_goals"], incoming["penalty_team_b_goals"]
    return incoming["penalty_team_b_goals"], incoming["penalty_team_a_goals"]


def _validate_knockout_progression(
    fixture: dict[str, Any],
    fixtures: list[dict[str, Any]],
) -> None:
    stage = str(fixture.get("stage"))
    if stage == "Round of 32":
        return
    allowed_winners = winners_from_previous_round(fixtures, stage)
    if not allowed_winners:
        return
    for team_id in (fixture["team_a_id"], fixture["team_b_id"]):
        if team_id not in allowed_winners:
            raise ResultsSyncError(
                f"Knockout progression guard rejected {fixture['id']}: "
                f"{team_id} has not won the previous round."
            )


def _result_record(
    fixture: dict[str, Any],
    existing_sources: dict[str, str],
) -> dict[str, Any]:
    result = fixture["result"]
    record = {
        "match_id": fixture["id"],
        "team_a_id": fixture["team_a_id"],
        "team_b_id": fixture["team_b_id"],
        "team_a_goals": result["team_a_goals"],
        "team_b_goals": result["team_b_goals"],
        "status": "finished",
        "source": fixture.get(
            "result_source",
            existing_sources.get(fixture["id"], "previous published result"),
        ),
        "stage": fixture.get("stage", "group"),
    }
    if result.get("decided_by_penalties"):
        record["decided_by_penalties"] = True
        record["penalty_team_a_goals"] = result.get("penalty_team_a_goals")
        record["penalty_team_b_goals"] = result.get("penalty_team_b_goals")
    return record


def _append_materialized_knockout_fixtures(
    fixtures: list[dict[str, Any]],
    teams: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    from app.models.domain import Match
    from app.services.data_loader import load_tournament

    base_config = load_tournament("processed")
    matches = [Match.model_validate(fixture) for fixture in fixtures]
    config = base_config.model_copy(update={"matches": matches})
    new_matches = materialize_pending_knockout_rounds(config)
    if not new_matches:
        return fixtures
    serialized = [
        {
            "id": match.id,
            "stage": match.stage,
            "team_a_id": match.team_a_id,
            "team_b_id": match.team_b_id,
            "result": None,
            "winner_team_id": None,
            "status": "scheduled",
        }
        for match in new_matches
    ]
    return [*fixtures, *serialized]


def _orient_score(
    fixture: dict[str, Any],
    incoming: dict[str, Any],
) -> tuple[int, int]:
    if (
        fixture["team_a_id"] == incoming["team_a_id"]
        and fixture["team_b_id"] == incoming["team_b_id"]
    ):
        return incoming["team_a_goals"], incoming["team_b_goals"]
    return incoming["team_b_goals"], incoming["team_a_goals"]


def _stage_metadata(staged_dir: Path, timestamp: str, provider: str) -> None:
    metadata = _read_json(staged_dir / "metadata.json")
    metadata["last_updated"] = timestamp
    metadata["data_version"] = f"2026-worldcup-results-{timestamp[:10]}"
    metadata["result_source"] = provider
    _write_json(staged_dir / "metadata.json", metadata)


def _stage_data_quality(
    staged_dir: Path,
    timestamp: str,
    completed_result_count: int,
) -> None:
    quality = _read_json(staged_dir / "data_quality.json")
    quality["last_refresh"] = timestamp
    quality.setdefault("source_coverage", {})["completed_results"] = (
        completed_result_count
    )
    _write_json(staged_dir / "data_quality.json", quality)


def _validate_staged_data(staged_dir: Path) -> list[str]:
    import sys

    ingest_dir = REPO_ROOT / "scripts" / "ingest"
    if str(ingest_dir) not in sys.path:
        sys.path.insert(0, str(ingest_dir))
    from validate_processed_data import validate_processed_data

    return validate_processed_data(staged_dir)


def _publish_files(staged_dir: Path) -> str:
    return publish_data_snapshot(staged_dir)


def _append_probability_snapshot(
    timestamp: str,
    champion_probabilities: dict[str, float],
) -> None:
    try:
        from app.services.data_sync_service import _current_matchday
        history_path = _active_processed_dir() / "probability_history.json"
        history = _read_json(history_path) if history_path.exists() else []
        history.append(
            {
                "timestamp": timestamp,
                "matchday": _current_matchday(),
                "champion_probabilities": champion_probabilities,
            }
        )
        _write_json(history_path, history)
    except Exception:
        return


def _refresh_forecast_snapshot() -> ForecastSnapshotResponse:
    """Rebuild shared forecast after a successful result publication."""
    from app.services.forecast_snapshot_service import publish_forecast_snapshot

    return publish_forecast_snapshot("processed")


def _current_last_updated() -> str:
    metadata_path = _active_processed_dir() / "metadata.json"
    if not metadata_path.exists():
        return datetime.now(tz=UTC).replace(microsecond=0).isoformat()
    return str(_read_json(metadata_path).get("last_updated") or "")


def _team_pair(team_a_id: str, team_b_id: str) -> tuple[str, str]:
    return tuple(sorted((team_a_id, team_b_id)))


def _normalize(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode()
    )
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

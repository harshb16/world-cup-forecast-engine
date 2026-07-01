"""HTTP routes for the API."""

from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import DEFAULT_MODEL_TYPE, get_data_mode
from app.models.domain import Group, Match, Team
from app.models.schemas import (
    BracketSimulateRequest,
    BracketSimulationResponse,
    CurrentTournamentScoringResponse,
    DataMetadataResponse,
    DataQualityResponse,
    DataStatusResponse,
    DiagnosticSimulateRequest,
    ForecastSnapshotResponse,
    ForecastStatusResponse,
    GroupChaosResponse,
    HeadToHeadResponse,
    HistoricalBacktestResponse,
    HealthResponse,
    MatchdayResponse,
    ModelComparisonResponse,
    ModelMetadataResponse,
    ModelType,
    ProbabilityHistoryResponse,
    ProbabilityMoversResponse,
    RollbackResponse,
    ScenarioCompareResponse,
    ScenarioSimulateRequest,
    SimulateRequest,
    SimulationSummaryResponse,
    SnapshotRecordResponse,
    SyncJobDetailResponse,
    SyncJobStartResponse,
    ThirdPlaceTrackerResponse,
    TeamPathRequest,
    TeamPathResponse,
    UpsetRadarResponse,
)
from app.services.analytics_service import (
    calculate_group_chaos,
    calculate_model_comparison,
    calculate_upset_radar,
)
from app.services.backtest_service import calculate_historical_backtest
from app.services.bracket_service import run_bracket_simulation
from app.services.current_tournament_scoring import (
    calculate_current_tournament_scores,
)
from app.services.data_loader import get_processed_data_dir, load_metadata, load_tournament
from app.services.data_quality_service import calculate_data_quality
from app.services.data_status_service import build_data_status
from app.services.head_to_head_service import calculate_head_to_head
from app.services.forecast_snapshot_service import (
    load_forecast_snapshot,
    load_forecast_status,
)
from app.services.matchday_service import calculate_matchday
from app.services.model_metadata import list_model_metadata
from app.services.probability_movers_service import calculate_probability_movers
from app.services.probability_timeline_service import build_probability_timeline
from app.services.results_sync_service import (
    admin_key_is_valid,
    admin_sync_is_configured,
)
from app.services.runtime_store import (
    list_data_snapshots,
    list_forecast_snapshots,
    rollback_data_snapshot,
    rollback_forecast_snapshot,
)
from app.services.sync_job_service import (
    SyncJobAlreadyRunningError,
    SyncJobCooldownError,
    get_sync_job,
    start_sync_job,
)
from app.services.simulation_service import (
    run_scenario_compare,
    run_scenario_simulation,
    run_simulation,
    run_sample_scenario_compare,
    run_sample_scenario_simulation,
    run_sample_simulation,
)
from app.services.team_path_service import calculate_team_path, get_published_team_path
from app.services.third_place_tracker_service import calculate_third_place_tracker

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return API health status."""
    return HealthResponse(status="ok")


@router.get("/teams", response_model=list[Team])
def teams() -> list[Team]:
    """Return active tournament teams."""
    return load_tournament(get_data_mode()).teams


@router.get("/groups", response_model=list[Group])
def groups() -> list[Group]:
    """Return active tournament groups."""
    return load_tournament(get_data_mode()).groups


@router.get("/fixtures", response_model=list[Match])
def fixtures() -> list[Match]:
    """Return active tournament fixtures."""
    return load_tournament(get_data_mode()).matches


@router.get("/metadata", response_model=DataMetadataResponse)
def metadata() -> DataMetadataResponse:
    """Return active tournament data metadata."""
    return DataMetadataResponse.model_validate(load_metadata(get_data_mode()))


@router.get("/data/status", response_model=DataStatusResponse)
def data_status() -> DataStatusResponse:
    """Return provider freshness, match status counts, and sync scheduler state."""
    return build_data_status()


@router.get("/forecast/latest", response_model=ForecastSnapshotResponse)
def latest_forecast() -> ForecastSnapshotResponse:
    """Return precomputed forecast artifacts without rerunning simulations."""
    try:
        return load_forecast_snapshot()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/forecast/status", response_model=ForecastStatusResponse)
def forecast_status() -> ForecastStatusResponse:
    """Return lightweight forecast freshness metadata for polling clients."""
    try:
        return load_forecast_status()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/admin/sync/results",
    response_model=SyncJobStartResponse,
    status_code=202,
)
def sync_match_results(
    admin_key: str | None = Header(default=None, alias="X-WCO-Admin-Key"),
) -> SyncJobStartResponse:
    """Queue an authenticated background result-sync job."""
    if not admin_sync_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Admin result sync is not configured.",
        )
    if not admin_key_is_valid(admin_key):
        raise HTTPException(status_code=401, detail="Invalid admin sync key.")
    try:
        return start_sync_job()
    except SyncJobAlreadyRunningError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except SyncJobCooldownError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc


@router.get("/admin/sync/{job_id}", response_model=SyncJobDetailResponse)
def sync_job_status(
    job_id: str,
    admin_key: str | None = Header(default=None, alias="X-WCO-Admin-Key"),
) -> SyncJobDetailResponse:
    """Return progress and outcome for one async result-sync job."""
    if not admin_sync_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Admin result sync is not configured.",
        )
    if not admin_key_is_valid(admin_key):
        raise HTTPException(status_code=401, detail="Invalid admin sync key.")
    try:
        return get_sync_job(job_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Sync job not found.") from exc


@router.get("/admin/snapshots/data", response_model=list[SnapshotRecordResponse])
def list_data_snapshot_records(
    admin_key: str | None = Header(default=None, alias="X-WCO-Admin-Key"),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[SnapshotRecordResponse]:
    """List recent tournament data snapshots."""
    if not admin_sync_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Admin result sync is not configured.",
        )
    if not admin_key_is_valid(admin_key):
        raise HTTPException(status_code=401, detail="Invalid admin sync key.")
    return [
        SnapshotRecordResponse(
            id=row["id"],
            created_at=row["created_at"],
            is_active=bool(row["is_active"]),
        )
        for row in list_data_snapshots(limit=limit)
    ]


@router.get("/admin/snapshots/forecast", response_model=list[SnapshotRecordResponse])
def list_forecast_snapshot_records(
    admin_key: str | None = Header(default=None, alias="X-WCO-Admin-Key"),
    limit: int = Query(default=10, ge=1, le=50),
) -> list[SnapshotRecordResponse]:
    """List recent forecast snapshots."""
    if not admin_sync_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Admin result sync is not configured.",
        )
    if not admin_key_is_valid(admin_key):
        raise HTTPException(status_code=401, detail="Invalid admin sync key.")
    return [
        SnapshotRecordResponse(
            id=row["id"],
            created_at=row["created_at"],
            is_active=bool(row["is_active"]),
            snapshot_id=row.get("snapshot_id"),
            bank_path=row.get("bank_path"),
        )
        for row in list_forecast_snapshots(limit=limit)
    ]


@router.post("/admin/rollback/data/{snapshot_id}", response_model=RollbackResponse)
def rollback_data_snapshot_record(
    snapshot_id: str,
    admin_key: str | None = Header(default=None, alias="X-WCO-Admin-Key"),
) -> RollbackResponse:
    """Activate a previously published tournament data snapshot."""
    if not admin_sync_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Admin result sync is not configured.",
        )
    if not admin_key_is_valid(admin_key):
        raise HTTPException(status_code=401, detail="Invalid admin sync key.")
    try:
        rollback_data_snapshot(snapshot_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Data snapshot not found.") from exc
    return RollbackResponse(success=True, active_id=snapshot_id)


@router.post(
    "/admin/rollback/forecast/{record_id}",
    response_model=RollbackResponse,
)
def rollback_forecast_snapshot_record(
    record_id: str,
    admin_key: str | None = Header(default=None, alias="X-WCO-Admin-Key"),
) -> RollbackResponse:
    """Activate a previously published forecast snapshot."""
    if not admin_sync_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Admin result sync is not configured.",
        )
    if not admin_key_is_valid(admin_key):
        raise HTTPException(status_code=401, detail="Invalid admin sync key.")
    try:
        rollback_forecast_snapshot(record_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail="Forecast snapshot not found.",
        ) from exc
    return RollbackResponse(success=True, active_id=record_id)


@router.get("/models", response_model=list[ModelMetadataResponse])
def models() -> list[ModelMetadataResponse]:
    """Return public metadata for supported match models."""
    return list_model_metadata()


@router.get(
    "/evaluation/historical",
    response_model=HistoricalBacktestResponse,
)
def historical_backtest(
    tournament: str = Query(default="2022", pattern="^2022$"),
    model_type: ModelType = DEFAULT_MODEL_TYPE,
) -> HistoricalBacktestResponse:
    """Score model predictions against a fixed historical World Cup dataset."""
    return calculate_historical_backtest(tournament="2022", model_type=model_type)  # type: ignore[arg-type]


@router.get(
    "/evaluation/current",
    response_model=CurrentTournamentScoringResponse,
)
def current_tournament_scoring(
    model_type: ModelType = DEFAULT_MODEL_TYPE,
) -> CurrentTournamentScoringResponse:
    """Score model predictions against completed active-tournament fixtures."""
    return calculate_current_tournament_scores(model_type, get_data_mode())


@router.post("/simulate", response_model=SimulationSummaryResponse)
def simulate(request: DiagnosticSimulateRequest) -> SimulationSummaryResponse:
    """Run a capped diagnostic simulation. Published UI forecasts use snapshot banks."""
    return run_simulation(
        SimulateRequest(
            n_simulations=request.n_simulations,
            model_type=request.model_type,
            seed=request.seed,
        ),
        get_data_mode(),
    )


@router.post("/bracket/simulate", response_model=BracketSimulationResponse)
def bracket_simulate(request: BracketSimulateRequest) -> BracketSimulationResponse:
    """Run one revealable tournament bracket simulation."""
    try:
        return run_bracket_simulation(request, get_data_mode())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/team-path/head-to-head", response_model=HeadToHeadResponse)
def team_path_head_to_head(
    team_a: str,
    team_b: str,
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    n_simulations: int = Query(default=500, ge=1, le=5_000),
    seed: int = 42,
) -> HeadToHeadResponse:
    try:
        return calculate_head_to_head(
            team_a, team_b, get_data_mode(), model_type, n_simulations, seed
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/team-path/{team_id}", response_model=TeamPathResponse)
def team_path_from_forecast(team_id: str) -> TeamPathResponse:
    """Return bank-derived knockout path for one team from the active forecast."""
    try:
        return get_published_team_path(team_id, get_data_mode())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/team-path", response_model=TeamPathResponse)
def team_path(request: TeamPathRequest) -> TeamPathResponse:
    """Run live Monte Carlo team path simulation for diagnostics."""
    try:
        return calculate_team_path(request, get_data_mode())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/scenario/simulate", response_model=SimulationSummaryResponse)
def scenario_simulate(request: ScenarioSimulateRequest) -> SimulationSummaryResponse:
    """Run a what-if simulation against sample tournament data."""
    try:
        return run_scenario_simulation(request, get_data_mode())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/scenario/compare", response_model=ScenarioCompareResponse)
def scenario_compare(request: ScenarioSimulateRequest) -> ScenarioCompareResponse:
    """Compare baseline and what-if simulation probabilities."""
    try:
        return run_scenario_compare(request, get_data_mode())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analytics/upsets", response_model=UpsetRadarResponse)
def upset_radar(
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    limit: int = 12,
) -> UpsetRadarResponse:
    """Return ranked upset-risk fixtures for the active tournament."""
    return calculate_upset_radar(get_data_mode(), model_type, limit)


@router.get("/analytics/group-chaos", response_model=GroupChaosResponse)
def group_chaos(
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    n_simulations: int = 500,
    seed: int = 42,
) -> GroupChaosResponse:
    """Return group chaos scores from simulation output."""
    return calculate_group_chaos(
        get_data_mode(),
        model_type,
        n_simulations=n_simulations,
        seed=seed,
    )


@router.get("/analytics/model-comparison", response_model=ModelComparisonResponse)
def model_comparison(
    n_simulations: int = 300,
    seed: int = 42,
    baseline_model: ModelType = DEFAULT_MODEL_TYPE,
) -> ModelComparisonResponse:
    """Compare champion probabilities across supported models."""
    return calculate_model_comparison(
        get_data_mode(),
        n_simulations=n_simulations,
        seed=seed,
        baseline_model=baseline_model,
    )


@router.get("/analytics/probability-history", response_model=ProbabilityHistoryResponse)
def probability_history(
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    n_simulations: int = Query(default=500, ge=1, le=1_000),
    seed: int = 42,
) -> ProbabilityHistoryResponse:
    return build_probability_timeline(
        get_data_mode(),
        model_type=model_type,
        n_simulations=n_simulations,
        seed=seed,
    )


@router.get("/analytics/probability-movers", response_model=ProbabilityMoversResponse)
def probability_movers(
    limit: int = Query(default=8, ge=1, le=48),
) -> ProbabilityMoversResponse:
    return calculate_probability_movers(limit=limit)


@router.get("/analytics/third-place", response_model=ThirdPlaceTrackerResponse)
def third_place_tracker(
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    n_simulations: int = Query(default=500, ge=1, le=5_000),
    seed: int = 42,
) -> ThirdPlaceTrackerResponse:
    try:
        return calculate_third_place_tracker(
            get_data_mode(), model_type, n_simulations=n_simulations, seed=seed
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/data-quality", response_model=DataQualityResponse)
def data_quality() -> DataQualityResponse:
    """Return source coverage and missing feature warnings."""
    return calculate_data_quality(get_data_mode())


@router.get("/matchday", response_model=MatchdayResponse)
def matchday(model_type: ModelType = DEFAULT_MODEL_TYPE) -> MatchdayResponse:
    return calculate_matchday(get_data_mode(), model_type)

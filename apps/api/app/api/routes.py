"""HTTP routes for the API."""

import json

from fastapi import APIRouter, HTTPException

from app.core.config import DEFAULT_MODEL_TYPE, get_data_mode
from app.models.domain import Group, Match, Team
from app.models.schemas import (
    BacktestingResponse,
    BracketSimulateRequest,
    BracketSimulationResponse,
    DataMetadataResponse,
    DataQualityResponse,
    GroupChaosResponse,
    HeadToHeadResponse,
    HealthResponse,
    MatchdayResponse,
    ModelComparisonResponse,
    ModelMetadataResponse,
    ModelType,
    ProbabilityHistoryResponse,
    ProbabilityMoversResponse,
    ProbabilitySnapshotResponse,
    ScenarioCompareResponse,
    ScenarioSimulateRequest,
    SimulateRequest,
    SimulationSummaryResponse,
    SyncResponse,
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
from app.services.backtesting import calculate_backtesting_metrics
from app.services.bracket_service import run_bracket_simulation
from app.services.data_loader import load_metadata, load_tournament
from app.services.data_quality_service import calculate_data_quality
from app.services.data_sync_service import run_data_sync
from app.services.head_to_head_service import calculate_head_to_head
from app.services.matchday_service import calculate_matchday
from app.services.model_metadata import list_model_metadata
from app.services.probability_movers_service import calculate_probability_movers
from app.services.simulation_service import (
    run_scenario_compare,
    run_scenario_simulation,
    run_simulation,
    run_sample_scenario_compare,
    run_sample_scenario_simulation,
    run_sample_simulation,
)
from app.services.team_path_service import calculate_team_path
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


@router.get("/models", response_model=list[ModelMetadataResponse])
def models() -> list[ModelMetadataResponse]:
    """Return public metadata for supported match models."""
    return list_model_metadata()


@router.get("/backtesting", response_model=BacktestingResponse)
def backtesting(
    model_type: ModelType = DEFAULT_MODEL_TYPE,
) -> BacktestingResponse:
    """Return baseline backtesting metrics for completed fixtures."""
    return calculate_backtesting_metrics(model_type, get_data_mode())


@router.post("/simulate", response_model=SimulationSummaryResponse)
def simulate(request: SimulateRequest) -> SimulationSummaryResponse:
    """Run a Monte Carlo simulation against sample tournament data."""
    return run_simulation(request, get_data_mode())


@router.post("/bracket/simulate", response_model=BracketSimulationResponse)
def bracket_simulate(request: BracketSimulateRequest) -> BracketSimulationResponse:
    """Run one revealable tournament bracket simulation."""
    try:
        return run_bracket_simulation(request, get_data_mode())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/team-path", response_model=TeamPathResponse)
def team_path(request: TeamPathRequest) -> TeamPathResponse:
    """Return likely knockout path distribution for one team."""
    try:
        return calculate_team_path(request, get_data_mode())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/team-path/head-to-head", response_model=HeadToHeadResponse)
def team_path_head_to_head(
    team_a: str,
    team_b: str,
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    n_simulations: int = 500,
    seed: int = 42,
) -> HeadToHeadResponse:
    try:
        return calculate_head_to_head(
            team_a, team_b, get_data_mode(), model_type, n_simulations, seed
        )
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
def probability_history() -> ProbabilityHistoryResponse:
    import app.services.data_sync_service as data_sync_service

    history_path = data_sync_service.PROCESSED_DIR / "probability_history.json"
    if not history_path.exists():
        return ProbabilityHistoryResponse(snapshots=[])
    raw: list[dict] = json.loads(history_path.read_text(encoding="utf-8"))
    return ProbabilityHistoryResponse(
        snapshots=[ProbabilitySnapshotResponse(**entry) for entry in raw]
    )


@router.get("/analytics/probability-movers", response_model=ProbabilityMoversResponse)
def probability_movers(limit: int = 8) -> ProbabilityMoversResponse:
    return calculate_probability_movers(limit=limit)


@router.get("/analytics/third-place", response_model=ThirdPlaceTrackerResponse)
def third_place_tracker(
    model_type: ModelType = DEFAULT_MODEL_TYPE,
    n_simulations: int = 500,
    seed: int = 42,
) -> ThirdPlaceTrackerResponse:
    return calculate_third_place_tracker(
        get_data_mode(), model_type, n_simulations=n_simulations, seed=seed
    )


@router.get("/data-quality", response_model=DataQualityResponse)
def data_quality() -> DataQualityResponse:
    """Return source coverage and missing feature warnings."""
    return calculate_data_quality(get_data_mode())


@router.get("/matchday", response_model=MatchdayResponse)
def matchday(model_type: ModelType = DEFAULT_MODEL_TYPE) -> MatchdayResponse:
    return calculate_matchday(get_data_mode(), model_type)


@router.post("/sync", response_model=SyncResponse)
def sync_data() -> SyncResponse:
    """Re-run ingest scripts and refresh processed data."""
    return run_data_sync()

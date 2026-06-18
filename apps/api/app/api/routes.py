"""HTTP routes for the API."""

from fastapi import APIRouter, HTTPException

from app.core.config import get_data_mode
from app.models.domain import Group, Match, Team
from app.models.schemas import (
    BacktestingResponse,
    BracketSimulateRequest,
    BracketSimulationResponse,
    DataMetadataResponse,
    DataQualityResponse,
    GroupChaosResponse,
    HealthResponse,
    ModelComparisonResponse,
    ModelMetadataResponse,
    ModelType,
    ScenarioCompareResponse,
    ScenarioSimulateRequest,
    SimulateRequest,
    SimulationSummaryResponse,
    SyncResponse,
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
from app.services.model_metadata import list_model_metadata
from app.services.simulation_service import (
    run_scenario_compare,
    run_scenario_simulation,
    run_simulation,
    run_sample_scenario_compare,
    run_sample_scenario_simulation,
    run_sample_simulation,
)
from app.services.team_path_service import calculate_team_path

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
    model_type: ModelType = "oracle_v2",
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
    model_type: ModelType = "oracle_v2",
    limit: int = 12,
) -> UpsetRadarResponse:
    """Return ranked upset-risk fixtures for the active tournament."""
    return calculate_upset_radar(get_data_mode(), model_type, limit)


@router.get("/analytics/group-chaos", response_model=GroupChaosResponse)
def group_chaos(
    model_type: ModelType = "oracle_v2",
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
    baseline_model: ModelType = "oracle_v2",
) -> ModelComparisonResponse:
    """Compare champion probabilities across supported models."""
    return calculate_model_comparison(
        get_data_mode(),
        n_simulations=n_simulations,
        seed=seed,
        baseline_model=baseline_model,
    )


@router.get("/data-quality", response_model=DataQualityResponse)
def data_quality() -> DataQualityResponse:
    """Return source coverage and missing feature warnings."""
    return calculate_data_quality(get_data_mode())


@router.post("/sync", response_model=SyncResponse)
def sync_data() -> SyncResponse:
    """Re-run ingest scripts and refresh processed data."""
    return run_data_sync()

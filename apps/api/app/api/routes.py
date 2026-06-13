"""HTTP routes for the API."""

from typing import Literal

from fastapi import APIRouter, HTTPException

from app.core.config import get_data_mode
from app.models.domain import Group, Match, Team
from app.models.schemas import (
    BacktestingResponse,
    DataMetadataResponse,
    HealthResponse,
    ModelMetadataResponse,
    ScenarioCompareResponse,
    ScenarioSimulateRequest,
    SimulateRequest,
    SimulationSummaryResponse,
)
from app.services.backtesting import calculate_backtesting_metrics
from app.services.data_loader import load_metadata, load_tournament
from app.services.model_metadata import list_model_metadata
from app.services.simulation_service import (
    run_scenario_compare,
    run_scenario_simulation,
    run_simulation,
    run_sample_scenario_compare,
    run_sample_scenario_simulation,
    run_sample_simulation,
)

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
    model_type: Literal["elo", "poisson"] = "poisson",
) -> BacktestingResponse:
    """Return baseline backtesting metrics for completed fixtures."""
    return calculate_backtesting_metrics(model_type, get_data_mode())


@router.post("/simulate", response_model=SimulationSummaryResponse)
def simulate(request: SimulateRequest) -> SimulationSummaryResponse:
    """Run a Monte Carlo simulation against sample tournament data."""
    return run_simulation(request, get_data_mode())


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

"""HTTP routes for the API."""

from fastapi import APIRouter, HTTPException

from app.models.domain import Group, Match, Team
from app.models.schemas import (
    HealthResponse,
    ScenarioCompareResponse,
    ScenarioSimulateRequest,
    SimulateRequest,
    SimulationSummaryResponse,
)
from app.services.data_loader import load_sample_tournament
from app.services.simulation_service import (
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
    """Return sample tournament teams."""
    return load_sample_tournament().teams


@router.get("/groups", response_model=list[Group])
def groups() -> list[Group]:
    """Return sample tournament groups."""
    return load_sample_tournament().groups


@router.get("/fixtures", response_model=list[Match])
def fixtures() -> list[Match]:
    """Return sample tournament fixtures."""
    return load_sample_tournament().matches


@router.post("/simulate", response_model=SimulationSummaryResponse)
def simulate(request: SimulateRequest) -> SimulationSummaryResponse:
    """Run a Monte Carlo simulation against sample tournament data."""
    return run_sample_simulation(request)


@router.post("/scenario/simulate", response_model=SimulationSummaryResponse)
def scenario_simulate(request: ScenarioSimulateRequest) -> SimulationSummaryResponse:
    """Run a what-if simulation against sample tournament data."""
    try:
        return run_sample_scenario_simulation(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/scenario/compare", response_model=ScenarioCompareResponse)
def scenario_compare(request: ScenarioSimulateRequest) -> ScenarioCompareResponse:
    """Compare baseline and what-if simulation probabilities."""
    try:
        return run_sample_scenario_compare(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

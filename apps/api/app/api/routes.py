"""HTTP routes for the API."""

from fastapi import APIRouter

from app.models.domain import Group, Match, Team
from app.models.schemas import HealthResponse
from app.services.data_loader import load_sample_tournament

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

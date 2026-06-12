"""Pydantic schemas for API requests and responses."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response body for the health endpoint."""

    status: str


class SimulateRequest(BaseModel):
    """Request body for running a sample tournament simulation."""

    n_simulations: int = Field(default=1000, ge=1, le=10_000)
    model_type: Literal["elo", "poisson"] = "elo"
    seed: int | None = None


class MatchResultOverride(BaseModel):
    """Manual result override for one match."""

    match_id: str = Field(min_length=1)
    team_a_goals: int = Field(ge=0)
    team_b_goals: int = Field(ge=0)


class ScenarioSimulateRequest(SimulateRequest):
    """Request body for scenario simulation with match result overrides."""

    result_overrides: list[MatchResultOverride] = Field(default_factory=list)


class TeamStageProbabilityResponse(BaseModel):
    """Per-team probability response."""

    team_id: str
    team_name: str
    group_id: str
    group_stage_exit: float
    round_of_32: float
    round_of_16: float
    quarter_final: float
    semi_final: float
    final: float
    champion: float
    group_qualification_probability: float
    top_two_probability: float
    third_place_finish_probability: float
    third_place_qualification_probability: float
    average_points: float


class SimulationMetadataResponse(BaseModel):
    """Metadata describing a simulation response."""

    n_simulations: int
    model_type: str
    seed: int | None = None
    overrides_applied: list[MatchResultOverride] = Field(default_factory=list)


class SimulationSummaryResponse(BaseModel):
    """Frontend-friendly simulation summary response."""

    metadata: SimulationMetadataResponse
    teams: list[TeamStageProbabilityResponse]
    champion_probabilities: dict[str, float]
    group_qualification_probabilities: dict[str, float]
    top_two_probabilities: dict[str, float]
    third_place_finish_probabilities: dict[str, float]
    third_place_qualification_probabilities: dict[str, float]
    average_points_by_team: dict[str, float]


class TeamProbabilityDeltaResponse(BaseModel):
    """Per-team scenario probability deltas."""

    team_id: str
    team_name: str
    group_id: str
    champion_probability_delta: float
    final_probability_delta: float
    semi_final_probability_delta: float
    quarter_final_probability_delta: float
    round_of_16_probability_delta: float
    round_of_32_probability_delta: float
    group_qualification_probability_delta: float


class ScenarioCompareResponse(BaseModel):
    """Response body for comparing baseline and scenario simulations."""

    baseline: SimulationSummaryResponse
    scenario: SimulationSummaryResponse
    deltas: list[TeamProbabilityDeltaResponse]
    biggest_risers: list[TeamProbabilityDeltaResponse]
    biggest_fallers: list[TeamProbabilityDeltaResponse]

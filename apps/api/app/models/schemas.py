"""Pydantic schemas for API requests and responses."""

from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response body for the health endpoint."""

    status: str


class SimulateRequest(BaseModel):
    """Request body for running a sample tournament simulation."""

    n_simulations: int = Field(default=1000, ge=1, le=10_000)
    model_type: Literal["elo", "poisson", "calibrated_elo"] = "elo"
    seed: int | None = None


class MatchResultOverride(BaseModel):
    """Manual result override for one match."""

    match_id: str = Field(min_length=1)
    team_a_goals: int = Field(ge=0)
    team_b_goals: int = Field(ge=0)


class ScenarioSimulateRequest(SimulateRequest):
    """Request body for scenario simulation with match result overrides."""

    result_overrides: list[MatchResultOverride] = Field(default_factory=list)


class BracketSimulateRequest(BaseModel):
    """Request body for simulating one revealable tournament bracket."""

    model_type: Literal["elo", "poisson", "calibrated_elo"] = "poisson"
    simulation_mode: Literal["favorite", "random"] = "favorite"
    seed: int | None = None
    result_overrides: list[MatchResultOverride] = Field(default_factory=list)


class TeamPathRequest(BaseModel):
    """Request body for exploring a team's likely knockout path."""

    team_id: str = Field(min_length=1)
    model_type: Literal["elo", "poisson", "calibrated_elo"] = "poisson"
    n_simulations: int = Field(default=500, ge=1, le=5_000)
    seed: int | None = None


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
    data_mode: str = "processed"
    is_real_data: bool = True
    data_version: str | None = None
    last_updated: str | None = None
    sources: list[dict[str, object]] = Field(default_factory=list)
    rating_source: str | None = None
    ratings_are_official: bool = False
    bracket_status: str | None = None
    team_count: int | None = None
    group_count: int | None = None
    fixture_count: int | None = None
    completed_result_count: int | None = None
    rating_coverage_count: int | None = None
    data_quality_notes: list[str] = Field(default_factory=list)
    model_limitations: list[str] = Field(default_factory=list)


class DataMetadataResponse(BaseModel):
    """Metadata describing the active tournament data source."""

    data_mode: str
    is_real_data: bool
    data_version: str | None = None
    last_updated: str | None = None
    sources: list[dict[str, object]] = Field(default_factory=list)
    rating_source: str | None = None
    ratings_are_official: bool = False
    bracket_status: str | None = None
    team_count: int
    group_count: int
    fixture_count: int
    completed_result_count: int
    rating_coverage_count: int
    data_quality_notes: list[str] = Field(default_factory=list)
    model_limitations: list[str] = Field(default_factory=list)


class ModelMetadataResponse(BaseModel):
    """Public description of a supported match model."""

    id: Literal["elo", "poisson", "calibrated_elo"]
    name: str
    is_ml: bool
    inputs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    supported_outputs: list[str] = Field(default_factory=list)


class BacktestingResponse(BaseModel):
    """Baseline evaluation metrics for completed fixtures."""

    model_type: Literal["elo", "poisson", "calibrated_elo"]
    data_mode: str
    sample_size: int
    accuracy: float | None = None
    brier_score: float | None = None
    log_loss: float | None = None
    limitations: list[str] = Field(default_factory=list)


class BracketTeamResponse(BaseModel):
    """Team payload used inside a bracket match."""

    team_id: str
    team_name: str
    group_id: str
    rating: float


class BracketMatchProbabilityResponse(BaseModel):
    """Pre-match probabilities for a bracket match."""

    team_a_win: float
    draw: float
    team_b_win: float
    team_a_advance: float
    team_b_advance: float


class BracketMatchResponse(BaseModel):
    """One revealable knockout match."""

    id: str
    stage: str
    match_number: int
    team_a: BracketTeamResponse
    team_b: BracketTeamResponse
    result: dict[str, int]
    winner_team_id: str
    probabilities: BracketMatchProbabilityResponse


class BracketGroupTableResponse(BaseModel):
    """Final group table included with a bracket trace."""

    group_id: str
    rows: list[dict[str, object]]


class BracketSimulationResponse(BaseModel):
    """One complete tournament trace for an interactive bracket reveal."""

    metadata: SimulationMetadataResponse
    simulation_mode: Literal["favorite", "random"]
    group_tables: list[BracketGroupTableResponse]
    rounds: dict[str, list[BracketMatchResponse]]
    champion_team_id: str
    champion_team_name: str


class TeamPathOpponentResponse(BaseModel):
    """Likely opponent row for one stage."""

    team_id: str
    team_name: str
    count: int
    probability: float


class TeamPathStageResponse(BaseModel):
    """Likely path distribution for one knockout stage."""

    stage: str
    reached_count: int
    reached_probability: float
    opponents: list[TeamPathOpponentResponse] = Field(default_factory=list)


class TeamPathResponse(BaseModel):
    """Monte Carlo path explorer response for one team."""

    metadata: SimulationMetadataResponse
    team: BracketTeamResponse
    stages: list[TeamPathStageResponse]


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

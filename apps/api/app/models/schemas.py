"""Pydantic schemas for API requests and responses."""

from typing import Literal

from pydantic import BaseModel, Field

from app.core.config import DEFAULT_MODEL_TYPE

ModelType = Literal[
    "elo",
    "poisson",
    "calibrated_elo",
    "oracle_v2",
    "dixon_coles",
    "gbm",
    "oracle_v3",
]


class HealthResponse(BaseModel):
    """Response body for the health endpoint."""

    status: str


class SimulateRequest(BaseModel):
    """Request body for running a sample tournament simulation."""

    n_simulations: int = Field(default=1000, ge=1, le=10_000)
    model_type: ModelType = DEFAULT_MODEL_TYPE
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

    model_type: ModelType = DEFAULT_MODEL_TYPE
    simulation_mode: Literal["favorite", "random"] = "favorite"
    seed: int | None = None
    result_overrides: list[MatchResultOverride] = Field(default_factory=list)


class TeamPathRequest(BaseModel):
    """Request body for exploring a team's likely knockout path."""

    team_id: str = Field(min_length=1)
    model_type: ModelType = DEFAULT_MODEL_TYPE
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

    id: ModelType
    name: str
    is_ml: bool
    maturity: Literal["baseline", "production", "experimental"]
    inputs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    supported_outputs: list[str] = Field(default_factory=list)


class CalibrationBinResponse(BaseModel):
    """One probability bucket for predicted vs actual outcome frequency."""

    predicted_midpoint: float
    actual_frequency: float
    count: int


class CurrentTournamentMatchScoreResponse(BaseModel):
    """Per-match score against a completed current-tournament fixture."""

    match_id: str
    predicted_outcome: str
    actual_outcome: str
    confidence: float


class CurrentTournamentScoringResponse(BaseModel):
    """Model scores against completed fixtures in the active tournament."""

    model_type: ModelType
    data_mode: str
    sample_size: int
    accuracy: float | None = None
    brier_score: float | None = None
    log_loss: float | None = None
    calibration_bins: list[CalibrationBinResponse] = Field(default_factory=list)
    per_match_details: list[CurrentTournamentMatchScoreResponse] = Field(
        default_factory=list
    )
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
    source_match_ids: list[str] = Field(default_factory=list)
    team_a: BracketTeamResponse
    team_b: BracketTeamResponse
    result: dict[str, int]
    winner_team_id: str
    probabilities: BracketMatchProbabilityResponse
    team_a_expected_goals: float | None = None
    team_b_expected_goals: float | None = None
    confidence_label: str | None = None
    drivers: list[str] = Field(default_factory=list)
    confirmed: bool = False


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


class TeamPathMostLikelyOpponentResponse(BaseModel):
    """Most likely opponent at one knockout stage."""

    team_id: str
    team_name: str
    probability: float


class TeamPathStageResponse(BaseModel):
    """Likely path distribution for one knockout stage."""

    stage: str
    reached_count: int
    reached_probability: float
    opponents: list[TeamPathOpponentResponse] = Field(default_factory=list)
    most_likely_opponent: TeamPathMostLikelyOpponentResponse | None = None


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


class UpsetFixtureResponse(BaseModel):
    """One ranked upset-risk fixture."""

    match_id: str
    stage: str
    group_id: str | None = None
    team_a_id: str
    team_a_name: str
    team_b_id: str
    team_b_name: str
    favorite_team_id: str
    underdog_team_id: str
    favorite_advance_probability: float
    underdog_advance_probability: float
    advance_probability_gap: float
    upset_score: float
    risk_label: str
    stage_importance: float
    reasons: list[str] = Field(default_factory=list)


class UpsetRadarResponse(BaseModel):
    """Ranked upset-risk fixtures for the active tournament."""

    model_type: ModelType
    data_mode: str
    fixtures: list[UpsetFixtureResponse]


class GroupChaosScoreResponse(BaseModel):
    """Chaos metrics for one group."""

    group_id: str
    group_name: str
    chaos_score: float
    chaos_label: str
    qualification_entropy: float
    average_point_spread: float
    key_swing_match_id: str | None = None
    key_swing_match_label: str | None = None
    teams: list[dict[str, object]] = Field(default_factory=list)


class GroupChaosResponse(BaseModel):
    """Group chaos scores derived from simulation output."""

    model_type: ModelType
    data_mode: str
    n_simulations: int
    groups: list[GroupChaosScoreResponse]


class ModelComparisonDeltaResponse(BaseModel):
    """Champion probability deltas versus a baseline model."""

    model_type: ModelType
    baseline_model: ModelType
    champion_probability_deltas: dict[str, float]
    top_four_probability_deltas: dict[str, float]
    largest_positive_delta_team_id: str
    largest_negative_delta_team_id: str


class ModelComparisonResponse(BaseModel):
    """Cross-model champion probability comparison."""

    data_mode: str
    n_simulations: int
    seed: int
    baseline_model: ModelType
    champion_probabilities: dict[str, dict[str, float]]
    top_four_team_ids: list[str]
    model_deltas: list[ModelComparisonDeltaResponse]


class TeamDataQualityResponse(BaseModel):
    """Coverage report for one team."""

    team_id: str
    team_name: str
    group_id: str
    has_rating: bool
    has_squad_features: bool
    squad_coverage: float | None = None
    alias_confidence: float | None = None
    missing_features: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DataQualityResponse(BaseModel):
    """Coverage report for active tournament data sources."""

    data_mode: str
    last_refresh: str
    source_coverage: dict[str, int]
    teams: list[TeamDataQualityResponse]
    missing_squad_features: list[str] = Field(default_factory=list)
    missing_ratings: list[str] = Field(default_factory=list)
    low_alias_coverage: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SyncResponse(BaseModel):
    """Response body for processed data sync."""

    success: bool
    last_updated: str
    errors: list[str] = Field(default_factory=list)


class ProbabilitySnapshotResponse(BaseModel):
    """One probability snapshot recorded after a sync."""

    timestamp: str
    matchday: int = 1
    champion_probabilities: dict[str, float]


class ProbabilityHistoryResponse(BaseModel):
    """Full history of probability snapshots."""

    snapshots: list[ProbabilitySnapshotResponse]


class ProbabilityMoverResponse(BaseModel):
    """Champion probability delta for one team."""

    team_id: str
    team_name: str
    previous_probability: float
    current_probability: float
    delta: float


class ProbabilityMoversResponse(BaseModel):
    """Top champion probability risers and fallers."""

    risers: list[ProbabilityMoverResponse]
    fallers: list[ProbabilityMoverResponse]
    previous_timestamp: str | None = None
    current_timestamp: str | None = None


class MatchdayFixtureResponse(BaseModel):
    """One fixture on the matchday page."""

    match_id: str
    group_id: str | None = None
    kickoff_utc: str | None = None
    status: str
    stage: str
    team_a_id: str
    team_a_name: str
    team_b_id: str
    team_b_name: str
    team_a_win_probability: float
    draw_probability: float
    team_b_win_probability: float
    projected_team_a_goals: float
    projected_team_b_goals: float
    team_a_goals: int | None = None
    team_b_goals: int | None = None
    what_still_matters: bool = False


class MatchdayGroupStanding(BaseModel):
    """One row in a matchday group standing table."""

    position: int
    team_id: str
    team_name: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class MatchdayGroupResponse(BaseModel):
    """Group standing table for the matchday page."""

    group_id: str
    group_name: str
    standings: list[MatchdayGroupStanding]
    is_complete: bool = False


class MatchdayResponse(BaseModel):
    """Response body for the GET /matchday endpoint."""

    date: str
    matchday_label: str
    model_type: ModelType
    fixtures: list[MatchdayFixtureResponse]
    groups: list[MatchdayGroupResponse]


class ThirdPlaceSlotDistributionResponse(BaseModel):
    """Knockout slot assignment probability for one third-place candidate."""

    slot_label: str
    probability: float


class ThirdPlaceTeamResponse(BaseModel):
    """One third-place qualification candidate."""

    team_id: str
    team_name: str
    group_id: str
    qualification_probability: float
    current_points: int
    simulated_average_points: float
    slot_distribution: list[ThirdPlaceSlotDistributionResponse] = Field(default_factory=list)


class ThirdPlaceTrackerResponse(BaseModel):
    """Ranked third-place qualification bubble."""

    model_type: ModelType
    data_mode: str
    n_simulations: int
    teams: list[ThirdPlaceTeamResponse]


class HeadToHeadResponse(BaseModel):
    """Probability of two teams meeting at a knockout stage."""

    team_a_id: str
    team_a_name: str
    team_b_id: str
    team_b_name: str
    probability: float = 0.0
    stages_they_could_meet: list[str] = Field(default_factory=list)
    meet_before_final_probability: float = 0.0
    meet_in_semi_final_probability: float = 0.0
    meet_in_final_probability: float = 0.0
    n_simulations: int

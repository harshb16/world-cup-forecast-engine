import { API_BASE_URL, TEAM_PATH_SIMULATION_COUNT } from "@/lib/config";
export { formatPercent } from "@/lib/format";

export type ModelType =
  | "elo"
  | "poisson"
  | "calibrated_elo"
  | "oracle_v2"
  | "dixon_coles"
  | "gbm"
  | "oracle_v3";

export const DEFAULT_MODEL_TYPE: ModelType = "calibrated_elo";

export type SimulationRequest = {
  n_simulations: number;
  model_type: ModelType;
  seed?: number;
};

export type TeamProbability = {
  team_id: string;
  team_name: string;
  group_id: string;
  group_stage_exit: number;
  round_of_32: number;
  round_of_16: number;
  quarter_final: number;
  semi_final: number;
  final: number;
  champion: number;
  group_qualification_probability: number;
  top_two_probability: number;
  third_place_finish_probability: number;
  third_place_qualification_probability: number;
  average_points: number;
};

export type Team = {
  id: string;
  name: string;
  group_id: string;
  rating: number;
};

export type Group = {
  id: string;
  name: string;
  team_ids: string[];
};

export type Match = {
  id: string;
  stage: string;
  group_id: string | null;
  team_a_id: string;
  team_b_id: string;
  result: {
    team_a_goals: number;
    team_b_goals: number;
    played: boolean;
  } | null;
  winner_team_id: string | null;
};

export type MatchResultOverride = {
  match_id: string;
  team_a_goals: number;
  team_b_goals: number;
};

export type DataMetadata = {
  data_mode: string;
  is_real_data: boolean;
  data_version: string | null;
  last_updated: string | null;
  sources: Array<Record<string, unknown>>;
  rating_source: string | null;
  result_source: string | null;
  ratings_are_official: boolean;
  bracket_status: string | null;
  team_count: number;
  group_count: number;
  fixture_count: number;
  completed_result_count: number;
  rating_coverage_count: number;
  data_quality_notes: string[];
  model_limitations: string[];
};

export type ProviderStatus = {
  name: string;
  configured: boolean;
  is_primary: boolean;
  last_used: string | null;
};

export type DataStatus = {
  metadata: DataMetadata;
  match_status_counts: Record<"scheduled" | "in_play" | "finished", number>;
  providers: ProviderStatus[];
  tournament_active: boolean;
  scheduler_active_interval_minutes: number;
  scheduler_idle_interval_minutes: number;
  recommended_interval_minutes: number;
  admin_sync_configured: boolean;
  latest_job: SyncJobDetail | null;
};

export type ResultsSyncResponse = {
  success: boolean;
  last_updated: string;
  provider: string | null;
  completed_result_count: number | null;
  changed_fixture_count: number;
  errors: string[];
};

export type SyncJobStart = {
  job_id: string;
  status: "queued" | "running" | "succeeded" | "failed" | "rejected";
};

export type SyncJobDetail = {
  job_id: string;
  status: SyncJobStart["status"];
  stage:
    | "queued"
    | "fetch"
    | "normalize"
    | "compare"
    | "validate"
    | "forecast"
    | "publish"
    | "done";
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  provider: string | null;
  completed_result_count: number | null;
  changed_fixture_count: number | null;
  conflicts: string[];
  errors: string[];
  result: ResultsSyncResponse | null;
};

export type ModelMetadata = {
  id: ModelType;
  name: string;
  is_ml: boolean;
  maturity: "baseline" | "production" | "experimental";
  inputs: string[];
  assumptions: string[];
  limitations: string[];
  supported_outputs: string[];
};

export type CurrentTournamentScoring = {
  model_type: ModelType;
  data_mode: string;
  sample_size: number;
  accuracy: number | null;
  brier_score: number | null;
  log_loss: number | null;
  calibration_bins: CalibrationBin[];
  per_match_details: CurrentTournamentMatchScore[];
  limitations: string[];
};

export type CalibrationBin = {
  predicted_midpoint: number;
  actual_frequency: number;
  count: number;
};

export type CurrentTournamentMatchScore = {
  match_id: string;
  predicted_outcome: string;
  actual_outcome: string;
  confidence: number;
};

export type BracketTeam = {
  team_id: string;
  team_name: string;
  group_id: string;
  rating: number;
};

export type BracketMatchProbabilities = {
  team_a_win: number;
  draw: number;
  team_b_win: number;
  team_a_advance: number;
  team_b_advance: number;
};

export type BracketMatch = {
  id: string;
  stage: string;
  match_number: number;
  source_match_ids: string[];
  team_a: BracketTeam;
  team_b: BracketTeam;
  result: {
    team_a_goals: number;
    team_b_goals: number;
  };
  winner_team_id: string;
  probabilities: BracketMatchProbabilities;
  team_a_expected_goals: number | null;
  team_b_expected_goals: number | null;
  confidence_label: string | null;
  drivers: string[];
  confirmed: boolean;
};

export type BracketSimulation = {
  metadata: DataMetadata & {
    n_simulations: number;
    model_type: ModelType;
    seed: number | null;
    overrides_applied: unknown[];
  };
  simulation_mode: "favorite" | "random";
  group_tables: Array<{
    group_id: string;
    rows: Array<Record<string, unknown>>;
  }>;
  rounds: Record<string, BracketMatch[]>;
  champion_team_id: string;
  champion_team_name: string;
};

export type TeamPathOpponent = {
  team_id: string;
  team_name: string;
  count: number;
  probability: number;
};

export type TeamPathMostLikelyOpponent = {
  team_id: string;
  team_name: string;
  probability: number;
};

export type TeamPathStage = {
  stage: string;
  reached_count: number;
  reached_probability: number;
  opponents: TeamPathOpponent[];
  most_likely_opponent: TeamPathMostLikelyOpponent | null;
};

export type TeamPath = {
  metadata: DataMetadata & {
    n_simulations: number;
    model_type: ModelType;
    seed: number | null;
    overrides_applied: unknown[];
  };
  team: BracketTeam;
  stages: TeamPathStage[];
};

export type SimulationSummary = {
  metadata: DataMetadata & {
    n_simulations: number;
    model_type: ModelType;
    seed: number | null;
    overrides_applied: unknown[];
  };
  teams: TeamProbability[];
  champion_probabilities: Record<string, number>;
  group_qualification_probabilities: Record<string, number>;
  top_two_probabilities: Record<string, number>;
  third_place_finish_probabilities: Record<string, number>;
  third_place_qualification_probabilities: Record<string, number>;
  average_points_by_team: Record<string, number>;
};

export type TeamProbabilityDelta = {
  team_id: string;
  team_name: string;
  group_id: string;
  champion_probability_delta: number;
  final_probability_delta: number;
  semi_final_probability_delta: number;
  quarter_final_probability_delta: number;
  round_of_16_probability_delta: number;
  round_of_32_probability_delta: number;
  group_qualification_probability_delta: number;
};

export type ScenarioCompareResponse = {
  baseline: SimulationSummary;
  scenario: SimulationSummary;
  deltas: TeamProbabilityDelta[];
  biggest_risers: TeamProbabilityDelta[];
  biggest_fallers: TeamProbabilityDelta[];
};

export type UpsetFixture = {
  match_id: string;
  stage: string;
  group_id: string | null;
  team_a_id: string;
  team_a_name: string;
  team_b_id: string;
  team_b_name: string;
  favorite_team_id: string;
  underdog_team_id: string;
  favorite_advance_probability: number;
  underdog_advance_probability: number;
  advance_probability_gap: number;
  upset_score: number;
  risk_label: string;
  stage_importance: number;
  reasons: string[];
};

export type UpsetRadar = {
  model_type: ModelType;
  data_mode: string;
  fixtures: UpsetFixture[];
};

export type GroupChaosScore = {
  group_id: string;
  group_name: string;
  chaos_score: number;
  chaos_label: string;
  qualification_entropy: number;
  average_point_spread: number;
  key_swing_match_id: string | null;
  key_swing_match_label: string | null;
  teams: Array<{
    team_id: string;
    team_name: string;
    group_qualification_probability: number;
    top_two_probability: number;
    average_points: number;
  }>;
};

export type GroupChaosReport = {
  model_type: ModelType;
  data_mode: string;
  n_simulations: number;
  groups: GroupChaosScore[];
};

export type ForecastStatus = {
  snapshot_id: string;
  data_version: string | null;
  forecast_generated_at: string;
  data_updated_at: string | null;
  completed_result_count: number | null;
  model_type: ModelType;
  n_simulations: number;
};

export type ForecastUncertainty = {
  n_simulations: number;
  champion_standard_error: Record<string, number>;
};

export type ForecastFixtureOutlook = {
  match_id: string;
  group_id: string | null;
  kickoff_utc: string | null;
  team_a_id: string;
  team_a_name: string;
  team_b_id: string;
  team_b_name: string;
  team_a_win: number;
  draw: number;
  team_b_win: number;
  team_a_expected_goals: number;
  team_b_expected_goals: number;
};

export type ForecastSnapshot = {
  snapshot_id: string;
  generated_at: string;
  model_version: ModelType;
  summary: SimulationSummary;
  group_chaos: GroupChaosReport;
  upsets: UpsetRadar;
  third_place: ThirdPlaceTracker;
  bracket: BracketSimulation;
  featured_final: BracketMatch;
  upcoming_fixtures: ForecastFixtureOutlook[];
  uncertainty: ForecastUncertainty;
};

export type ModelComparisonDelta = {
  model_type: ModelType;
  baseline_model: ModelType;
  champion_probability_deltas: Record<string, number>;
  top_four_probability_deltas: Record<string, number>;
  largest_positive_delta_team_id: string;
  largest_negative_delta_team_id: string;
};

export type ModelComparison = {
  data_mode: string;
  n_simulations: number;
  seed: number;
  baseline_model: ModelType;
  champion_probabilities: Record<ModelType, Record<string, number>>;
  top_four_team_ids: string[];
  model_deltas: ModelComparisonDelta[];
};

export type TeamDataQuality = {
  team_id: string;
  team_name: string;
  group_id: string;
  has_rating: boolean;
  has_squad_features: boolean;
  squad_coverage: number | null;
  alias_confidence: number | null;
  missing_features: string[];
  warnings: string[];
};

export type DataQualityReport = {
  data_mode: string;
  last_refresh: string;
  source_coverage: Record<string, number>;
  teams: TeamDataQuality[];
  missing_squad_features: string[];
  missing_ratings: string[];
  low_alias_coverage: string[];
  warnings: string[];
  notes: string[];
};

export async function simulateTournament(
  request: SimulationRequest,
): Promise<SimulationSummary> {
  const response = await fetch(`${API_BASE_URL}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Simulation failed with status ${response.status}`);
  }

  return response.json();
}

export async function compareScenario(request: {
  n_simulations: number;
  model_type: ModelType;
  seed?: number;
  result_overrides: MatchResultOverride[];
}): Promise<ScenarioCompareResponse> {
  const response = await fetch(`${API_BASE_URL}/scenario/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Scenario comparison failed with status ${response.status}`);
  }

  return response.json();
}

export async function simulateBracket(request: {
  model_type: ModelType;
  simulation_mode?: "favorite" | "random";
  seed?: number;
  result_overrides?: MatchResultOverride[];
}): Promise<BracketSimulation> {
  const response = await fetch(`${API_BASE_URL}/bracket/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ...request,
      result_overrides: request.result_overrides ?? [],
    }),
  });

  if (!response.ok) {
    throw new Error(`Bracket simulation failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchTeams(): Promise<Team[]> {
  return fetchJson<Team[]>("/teams");
}

export async function fetchGroups(): Promise<Group[]> {
  return fetchJson<Group[]>("/groups");
}

export async function fetchFixtures(): Promise<Match[]> {
  return fetchJson<Match[]>("/fixtures");
}

export async function fetchMetadata(): Promise<DataMetadata> {
  return fetchJson<DataMetadata>("/metadata");
}

export async function fetchDataStatus(): Promise<DataStatus> {
  return fetchJson<DataStatus>("/data/status");
}

export async function fetchLatestForecast(): Promise<ForecastSnapshot> {
  return fetchJson<ForecastSnapshot>("/forecast/latest");
}

export async function fetchForecastStatus(): Promise<ForecastStatus> {
  return fetchJson<ForecastStatus>("/forecast/status");
}

export async function startSyncJob(adminKey: string): Promise<SyncJobStart> {
  const response = await fetch(`${API_BASE_URL}/admin/sync/results`, {
    method: "POST",
    headers: {
      "X-WCO-Admin-Key": adminKey,
    },
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail =
      typeof payload?.detail === "string"
        ? payload.detail
        : payload?.detail?.errors?.join(" ");
    throw new Error(detail || `Result sync failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchSyncJob(
  jobId: string,
  adminKey: string,
): Promise<SyncJobDetail> {
  const response = await fetch(`${API_BASE_URL}/admin/sync/${jobId}`, {
    headers: {
      "X-WCO-Admin-Key": adminKey,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail =
      typeof payload?.detail === "string"
        ? payload.detail
        : payload?.detail?.errors?.join(" ");
    throw new Error(detail || `Sync job lookup failed with status ${response.status}`);
  }

  return response.json();
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

export async function syncMatchResults(
  adminKey: string,
  onProgress?: (job: SyncJobDetail) => void,
): Promise<ResultsSyncResponse> {
  const started = await startSyncJob(adminKey);

  while (true) {
    const job = await fetchSyncJob(started.job_id, adminKey);
    onProgress?.(job);

    if (job.status === "succeeded" && job.result) {
      return job.result;
    }

    if (job.status === "failed" || job.status === "rejected") {
      throw new Error(job.errors.join(" ") || "Result sync failed.");
    }

    await sleep(1_000);
  }
}

export async function fetchModelMetadata(): Promise<ModelMetadata[]> {
  return fetchJson<ModelMetadata[]>("/models");
}

export async function fetchCurrentTournamentScoring(
  modelType: ModelType = DEFAULT_MODEL_TYPE,
): Promise<CurrentTournamentScoring> {
  return fetchJson<CurrentTournamentScoring>(
    `/evaluation/current?model_type=${modelType}`,
  );
}

export async function fetchTeamPath(teamId: string): Promise<TeamPath> {
  const response = await fetch(`${API_BASE_URL}/team-path`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      team_id: teamId,
      model_type: DEFAULT_MODEL_TYPE,
      n_simulations: TEAM_PATH_SIMULATION_COUNT,
      seed: 42,
    }),
  });

  if (!response.ok) {
    throw new Error(`Team path request failed with status ${response.status}`);
  }

  return response.json();
}

export async function fetchUpsetRadar(
  modelType: ModelType = DEFAULT_MODEL_TYPE,
  limit = 8,
): Promise<UpsetRadar> {
  return fetchJson<UpsetRadar>(
    `/analytics/upsets?model_type=${modelType}&limit=${limit}`,
  );
}

export async function fetchGroupChaos(
  modelType: ModelType = DEFAULT_MODEL_TYPE,
  nSimulations = 500,
  seed = 42,
): Promise<GroupChaosReport> {
  return fetchJson<GroupChaosReport>(
    `/analytics/group-chaos?model_type=${modelType}&n_simulations=${nSimulations}&seed=${seed}`,
  );
}

export async function fetchModelComparison(
  nSimulations = 300,
  seed = 42,
  baselineModel: ModelType = DEFAULT_MODEL_TYPE,
): Promise<ModelComparison> {
  return fetchJson<ModelComparison>(
    `/analytics/model-comparison?n_simulations=${nSimulations}&seed=${seed}&baseline_model=${baselineModel}`,
  );
}

export async function fetchDataQuality(): Promise<DataQualityReport> {
  return fetchJson<DataQualityReport>("/data-quality");
}

export async function fetchProbabilityHistory(): Promise<ProbabilityHistory> {
  return fetchJson<ProbabilityHistory>("/analytics/probability-history");
}

export async function fetchProbabilityMovers(
  limit = 8,
): Promise<ProbabilityMovers> {
  return fetchJson<ProbabilityMovers>(
    `/analytics/probability-movers?limit=${limit}`,
  );
}

export async function fetchMatchday(
  modelType: ModelType = DEFAULT_MODEL_TYPE,
): Promise<MatchdayData> {
  return fetchJson<MatchdayData>(`/matchday?model_type=${modelType}`);
}

export async function fetchThirdPlaceTracker(
  modelType: ModelType = DEFAULT_MODEL_TYPE,
  nSimulations = 500,
  seed = 42,
): Promise<ThirdPlaceTracker> {
  return fetchJson<ThirdPlaceTracker>(
    `/analytics/third-place?model_type=${modelType}&n_simulations=${nSimulations}&seed=${seed}`,
  );
}

export async function fetchHeadToHead(
  teamAId: string,
  teamBId: string,
  modelType: ModelType = DEFAULT_MODEL_TYPE,
): Promise<HeadToHead> {
  return fetchJson<HeadToHead>(
    `/team-path/head-to-head?team_a=${teamAId}&team_b=${teamBId}&model_type=${modelType}`,
  );
}

export type ProbabilityMover = {
  team_id: string;
  team_name: string;
  previous_probability: number;
  current_probability: number;
  delta: number;
};

export type ProbabilityMovers = {
  risers: ProbabilityMover[];
  fallers: ProbabilityMover[];
  previous_timestamp: string | null;
  current_timestamp: string | null;
};

export type ProbabilitySnapshot = {
  timestamp: string;
  matchday: number | null;
  champion_probabilities: Record<string, number>;
};

export type ProbabilityHistory = {
  snapshots: ProbabilitySnapshot[];
};

export type MatchdayFixture = {
  match_id: string;
  group_id: string | null;
  kickoff_utc: string | null;
  status: string;
  stage: string;
  team_a_id: string;
  team_a_name: string;
  team_b_id: string;
  team_b_name: string;
  team_a_win_probability: number;
  draw_probability: number;
  team_b_win_probability: number;
  projected_team_a_goals: number;
  projected_team_b_goals: number;
  team_a_goals: number | null;
  team_b_goals: number | null;
  what_still_matters: boolean;
};

export type MatchdayGroupStanding = {
  position: number;
  team_id: string;
  team_name: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_difference: number;
  points: number;
};

export type MatchdayGroup = {
  group_id: string;
  group_name: string;
  standings: MatchdayGroupStanding[];
  is_complete: boolean;
};

export type MatchdayData = {
  date: string;
  matchday_label: string;
  model_type: ModelType;
  fixtures: MatchdayFixture[];
  groups: MatchdayGroup[];
};

export type ThirdPlaceSlotDistribution = {
  slot_label: string;
  probability: number;
};

export type ThirdPlaceTeam = {
  team_id: string;
  team_name: string;
  group_id: string;
  qualification_probability: number;
  current_points: number;
  simulated_average_points: number;
  slot_distribution: ThirdPlaceSlotDistribution[];
};

export type ThirdPlaceTracker = {
  model_type: ModelType;
  data_mode: string;
  n_simulations: number;
  teams: ThirdPlaceTeam[];
};

export type HeadToHead = {
  team_a_id: string;
  team_a_name: string;
  team_b_id: string;
  team_b_name: string;
  probability: number;
  stages_they_could_meet: string[];
  meet_before_final_probability: number;
  meet_in_semi_final_probability: number;
  meet_in_final_probability: number;
  n_simulations: number;
};

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

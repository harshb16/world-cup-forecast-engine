import { API_BASE_URL } from "@/lib/config";
export { formatPercent } from "@/lib/format";

export type ModelType = "elo" | "poisson";

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

export type SimulationSummary = {
  metadata: {
    n_simulations: number;
    model_type: ModelType;
    seed: number | null;
    overrides_applied: unknown[];
    data_mode: string;
    is_real_data: boolean;
    data_version: string | null;
    last_updated: string | null;
    sources: Array<Record<string, unknown>>;
    rating_source: string | null;
    ratings_are_official: boolean;
    bracket_status: string | null;
  };
  teams: TeamProbability[];
  champion_probabilities: Record<string, number>;
  group_qualification_probabilities: Record<string, number>;
  top_two_probabilities: Record<string, number>;
  third_place_finish_probabilities: Record<string, number>;
  third_place_qualification_probabilities: Record<string, number>;
  average_points_by_team: Record<string, number>;
};

export type DataMetadata = {
  data_mode: string;
  is_real_data: boolean;
  data_version: string | null;
  last_updated: string | null;
  sources: Array<Record<string, unknown>>;
  rating_source: string | null;
  ratings_are_official: boolean;
  bracket_status: string | null;
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

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

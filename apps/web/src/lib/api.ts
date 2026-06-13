import { API_BASE_URL } from "@/lib/config";

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

export type SimulationSummary = {
  metadata: {
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

export function formatPercent(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

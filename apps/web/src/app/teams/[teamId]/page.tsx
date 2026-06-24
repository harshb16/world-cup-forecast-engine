import type { Metadata } from "next";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { TeamDetailDashboard } from "@/components/teams/TeamDetailDashboard";
import { API_BASE_URL, SIMULATION_COUNT } from "@/lib/config";
import { DEFAULT_MODEL_TYPE } from "@/lib/api";

type TeamDetailPageProps = {
  params: Promise<{ teamId: string }>;
};

export async function generateMetadata({
  params,
}: TeamDetailPageProps): Promise<Metadata> {
  const { teamId } = await params;

  try {
    const [teamsResponse, simulationResponse] = await Promise.all([
      fetch(`${API_BASE_URL}/teams`, { next: { revalidate: 300 } }),
      fetch(`${API_BASE_URL}/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          n_simulations: SIMULATION_COUNT,
          model_type: DEFAULT_MODEL_TYPE,
          seed: 42,
        }),
        next: { revalidate: 300 },
      }),
    ]);

    if (!teamsResponse.ok || !simulationResponse.ok) {
      throw new Error("metadata fetch failed");
    }

    const teams = (await teamsResponse.json()) as Array<{
      id: string;
      name: string;
    }>;
    const simulation = (await simulationResponse.json()) as {
      champion_probabilities: Record<string, number>;
    };
    const team = teams.find((candidate) => candidate.id === teamId);
    const championProbability =
      simulation.champion_probabilities[teamId] ?? null;

    if (!team) {
      return {
        title: "Team not found | World Cup Oracle",
      };
    }

    const probabilityText =
      championProbability === null
        ? "champion odds unavailable"
        : `${Math.round(championProbability * 100)}% champion odds`;

    return {
      title: `${team.name} | World Cup Oracle`,
      description: `${team.name} — ${probabilityText} on checked-in World Cup 2026 data.`,
      openGraph: {
        title: `${team.name} | World Cup Oracle`,
        description: `${team.name} — ${probabilityText}.`,
      },
    };
  } catch {
    return {
      title: "Team profile | World Cup Oracle",
      description: "Team probability profile for World Cup 2026.",
    };
  }
}

export default function TeamDetailPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Team detail"
        title="Team probability profile"
        description="A team-level readout of rating, group position, qualification, and tournament upside."
      />
      <TeamDetailDashboard />
    </AppShell>
  );
}

"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import { fetchTeams } from "@/lib/api";

export function TeamDetailHeader() {
  const params = useParams<{ teamId: string }>();
  const [teamName, setTeamName] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;
    fetchTeams()
      .then((teams) => {
        if (!isActive) return;
        const team = teams.find((candidate) => candidate.id === params.teamId);
        setTeamName(team?.name ?? null);
      })
      .catch(() => {
        if (isActive) setTeamName(null);
      });
    return () => {
      isActive = false;
    };
  }, [params.teamId]);

  return (
    <PageHeader
      eyebrow="Team detail"
      title={teamName ?? "Team probability profile"}
      description="A team-level readout of rating, group position, qualification, and tournament upside."
    />
  );
}

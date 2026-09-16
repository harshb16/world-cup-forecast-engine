import { PageHeader } from "@/components/PageHeader";
import { TeamsDashboard } from "@/components/teams/TeamsDashboard";

export default function TeamsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Teams"
        title="Team dashboards"
        description="Search, filter by group, and open team profiles with stage-by-stage probability ladders."
      />
      <TeamsDashboard />
    </>
  );
}

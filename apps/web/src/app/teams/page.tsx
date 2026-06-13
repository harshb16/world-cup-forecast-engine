import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { TeamsDashboard } from "@/components/teams/TeamsDashboard";

export default function TeamsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Teams"
        title="Team index"
        description="Browse teams, ratings, group assignments, and latest simulation probabilities."
      />
      <TeamsDashboard />
    </AppShell>
  );
}

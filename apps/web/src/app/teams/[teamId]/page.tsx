import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { TeamDetailDashboard } from "@/components/teams/TeamDetailDashboard";

export default function TeamDetailPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Team detail"
        title="Team probability profile"
        description="Latest seeded simulation probabilities for this team."
      />
      <TeamDetailDashboard />
    </AppShell>
  );
}

import { AppShell } from "@/components/AppShell";
import { GroupsDashboard } from "@/components/groups/GroupsDashboard";
import { PageHeader } from "@/components/PageHeader";

export default function GroupsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Groups"
        title="Group qualification overview"
        description="Top-two odds, third-place paths, qualification probability, and average points by group."
      />
      <GroupsDashboard />
    </AppShell>
  );
}

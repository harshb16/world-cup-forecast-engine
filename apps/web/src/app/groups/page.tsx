import { AppShell } from "@/components/AppShell";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";

export default function GroupsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Groups"
        title="Group qualification overview"
        description="Group cards will combine team data with top-two and best third-place probabilities."
      />
      <LoadingState label="Group probability cards pending API connection" />
    </AppShell>
  );
}

import { AppShell } from "@/components/AppShell";
import { ProbabilityTimeline } from "@/components/analytics/ProbabilityTimeline";
import { PageHeader } from "@/components/PageHeader";

export default function TimelinePage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Timeline"
        title="Probability movement"
        description="Track how champion odds shifted after each sync snapshot."
      />
      <ProbabilityTimeline />
    </AppShell>
  );
}

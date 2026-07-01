import { ProbabilityTimeline } from "@/components/analytics/ProbabilityTimeline";
import { PageHeader } from "@/components/PageHeader";

export default function TimelinePage() {
  return (
    <>
      <PageHeader
        eyebrow="Timeline"
        title="Probability movement"
        description="Champion odds at each group matchday and knockout round as results are played."
      />
      <ProbabilityTimeline />
    </>
  );
}

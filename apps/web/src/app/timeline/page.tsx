import { ProbabilityTimeline } from "@/components/analytics/ProbabilityTimeline";
import { PageHeader } from "@/components/PageHeader";

export default function TimelinePage() {
  return (
    <>
      <PageHeader
        eyebrow="Timeline"
        title="Probability movement"
        description="Champion odds before and after each group matchday as results are played."
      />
      <ProbabilityTimeline />
    </>
  );
}

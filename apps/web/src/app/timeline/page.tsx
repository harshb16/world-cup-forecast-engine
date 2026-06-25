import { ProbabilityTimeline } from "@/components/analytics/ProbabilityTimeline";
import { PageHeader } from "@/components/PageHeader";

export default function TimelinePage() {
  return (
    <>
      <PageHeader
        eyebrow="Timeline"
        title="Probability movement"
        description="Track how champion odds shifted after each sync snapshot."
      />
      <ProbabilityTimeline />
    </>
  );
}

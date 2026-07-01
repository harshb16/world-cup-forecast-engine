import { RetrospectiveExperience } from "@/components/analytics/RetrospectiveExperience";
import { PageHeader } from "@/components/PageHeader";

export default function RetrospectivePage() {
  return (
    <>
      <PageHeader
        eyebrow="Retrospective"
        title="Tournament look-back"
        description="Champion arc, model hits and misses, and calibration across completed fixtures."
      />
      <RetrospectiveExperience />
    </>
  );
}

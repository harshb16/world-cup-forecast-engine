import { Suspense } from "react";

import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { TeamCompareDashboard } from "@/components/teams/TeamCompareDashboard";

export default function TeamComparePage() {
  return (
    <>
      <PageHeader
        eyebrow="Teams"
        title="Compare teams"
        description="Side-by-side champion odds, knockout paths, and meeting probability."
      />
      <Suspense fallback={<LoadingState label="Loading team comparison" />}>
        <TeamCompareDashboard />
      </Suspense>
    </>
  );
}

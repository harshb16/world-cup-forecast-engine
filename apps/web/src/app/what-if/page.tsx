import { Suspense } from "react";

import { AppShell } from "@/components/AppShell";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { WhatIfLab } from "@/components/scenario/WhatIfLab";

export default function WhatIfPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="What-if lab"
        title="Scenario simulation"
        description="Pick a few match results, rerun the model, and see which teams rise or fall."
      />
      <Suspense fallback={<LoadingState label="Loading scenario lab" />}>
        <WhatIfLab />
      </Suspense>
    </AppShell>
  );
}

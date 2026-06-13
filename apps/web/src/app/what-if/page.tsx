import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { WhatIfLab } from "@/components/scenario/WhatIfLab";

export default function WhatIfPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="What-if lab"
        title="Scenario simulation"
        description="Override match results and compare probability movement against the baseline."
      />
      <WhatIfLab />
    </AppShell>
  );
}

import type { Metadata } from "next";
import { Suspense } from "react";

import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { WhatIfLab } from "@/components/scenario/WhatIfLab";

type WhatIfPageProps = {
  searchParams: Promise<{ overrides?: string }>;
};

export async function generateMetadata({
  searchParams,
}: WhatIfPageProps): Promise<Metadata> {
  const params = await searchParams;
  const overrides = params.overrides;

  if (!overrides) {
    return {
      title: "What-if lab | World Cup Forecast Engine",
      description:
        "Override match results and compare tournament probabilities in the World Cup Forecast Engine what-if lab.",
      openGraph: {
        title: "What-if lab | World Cup Forecast Engine",
        description: "Explore scenario-driven probability shifts.",
      },
    };
  }

  return {
    title: "Shared what-if scenario | World Cup Forecast Engine",
    description: `Scenario with ${overrides.split(",").filter(Boolean).length} manual result override(s). Open to compare probability shifts.`,
    openGraph: {
      title: "Shared what-if scenario | World Cup Forecast Engine",
      description: "Open this shared scenario to compare tournament probability shifts.",
    },
  };
}

export default function WhatIfPage() {
  return (
    <>
      <PageHeader
        eyebrow="What-if lab"
        title="Scenario simulation"
        description="Pick a few match results, rerun the model, and see which teams rise or fall."
      />
      <Suspense fallback={<LoadingState label="Loading scenario lab" />}>
        <WhatIfLab />
      </Suspense>
    </>
  );
}

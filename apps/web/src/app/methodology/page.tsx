import type { Metadata } from "next";

import { AppShell } from "@/components/AppShell";
import { MethodologyExperience } from "@/components/methodology/MethodologyExperience";

export const metadata: Metadata = {
  title: "Methodology | World Cup Oracle",
  description:
    "How World Cup Oracle turns open football data into match and tournament probabilities.",
};

export default function MethodologyPage() {
  return (
    <AppShell>
      <MethodologyExperience />
    </AppShell>
  );
}

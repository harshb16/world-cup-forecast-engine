import type { Metadata } from "next";

import { MethodologyExperience } from "@/components/methodology/MethodologyExperience";

export const metadata: Metadata = {
  title: "Methodology | World Cup Forecast Engine",
  description:
    "How World Cup Forecast Engine turns open football data into match and tournament probabilities.",
};

export default function MethodologyPage() {
  return <MethodologyExperience />;
}

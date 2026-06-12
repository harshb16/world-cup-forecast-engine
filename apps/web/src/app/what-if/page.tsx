import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

export default function WhatIfPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="What-if lab"
        title="Scenario simulation"
        description="Manual match overrides will compare baseline and scenario probability movement."
      />
      <section className="rounded-lg border border-zinc-200 bg-white p-5">
        <h2 className="text-base font-semibold text-zinc-950">Scenario builder</h2>
        <p className="mt-2 text-sm text-zinc-600">
          Match selection and probability deltas will be added in this sprint.
        </p>
      </section>
    </AppShell>
  );
}

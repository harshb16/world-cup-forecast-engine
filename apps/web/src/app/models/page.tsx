import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

export default function ModelsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Models"
        title="Model comparison"
        description="Elo and Poisson model outputs will be compared here."
      />
      <section className="rounded-lg border border-zinc-200 bg-white p-5 text-sm text-zinc-600">
        Model comparison placeholder
      </section>
    </AppShell>
  );
}

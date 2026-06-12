import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

export default function TeamsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Teams"
        title="Team index"
        description="Searchable team cards and detail links will appear here."
      />
      <section className="rounded-lg border border-zinc-200 bg-white p-5 text-sm text-zinc-600">
        Team index placeholder
      </section>
    </AppShell>
  );
}

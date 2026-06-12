import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

export default function BacktestingPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Backtesting"
        title="Historical validation"
        description="Past tournament loaders and model scoring will be tracked here."
      />
      <section className="rounded-lg border border-zinc-200 bg-white p-5 text-sm text-zinc-600">
        Backtesting placeholder
      </section>
    </AppShell>
  );
}

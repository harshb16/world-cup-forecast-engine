import { Navigation } from "@/components/Navigation";
import { PageShell } from "@/components/ui/PageShell";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#070a12] text-zinc-100">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <Navigation />
        <main className="flex-1">
          <PageShell>{children}</PageShell>
        </main>
      </div>
    </div>
  );
}

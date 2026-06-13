import { Navigation } from "@/components/Navigation";
import { PageShell } from "@/components/ui/PageShell";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#05070a] text-[#f4f7f5]">
      <div className="flex min-h-screen flex-col lg:flex-row">
        <Navigation />
        <main className="flex-1 border-white/10 lg:border-l">
          <PageShell>{children}</PageShell>
        </main>
      </div>
    </div>
  );
}

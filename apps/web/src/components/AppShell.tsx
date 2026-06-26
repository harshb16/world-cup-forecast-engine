import { AppHeader } from "@/components/AppHeader";
import { AppMain } from "@/components/AppMain";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <AppHeader />
      <main className="flex-1">
        <AppMain>{children}</AppMain>
      </main>
    </div>
  );
}

import { AppHeader } from "@/components/AppHeader";
import { AppMain } from "@/components/AppMain";
import { ReplayTransport } from "@/components/time-machine/ReplayTransport";
import { TimeMachineProvider } from "@/components/time-machine/TimeMachineProvider";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <TimeMachineProvider>
      <div className="flex min-h-screen flex-col bg-background text-foreground">
        <AppHeader />
        <ReplayTransport />
        <main className="flex-1">
          <AppMain>{children}</AppMain>
        </main>
      </div>
    </TimeMachineProvider>
  );
}

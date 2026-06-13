import { AppShell } from "@/components/AppShell";
import { HomeDashboard } from "@/components/dashboard/HomeDashboard";
import { PageHeader } from "@/components/PageHeader";

export default function Home() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Tournament dashboard"
        title="World Cup simulation overview"
        description="Live simulation output from the backend API."
      />
      <HomeDashboard />
    </AppShell>
  );
}

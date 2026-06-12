import { AppShell } from "@/components/AppShell";
import { MetricCard } from "@/components/MetricCard";
import { PageHeader } from "@/components/PageHeader";

const winners = [
  { team: "Sample Team 01", probability: "14.2%" },
  { team: "Sample Team 02", probability: "11.8%" },
  { team: "Sample Team 03", probability: "9.4%" },
  { team: "Sample Team 04", probability: "8.1%" },
];

const stageRows = [
  { team: "Sample Team 01", r32: "91%", qf: "42%", final: "22%" },
  { team: "Sample Team 02", r32: "88%", qf: "37%", final: "18%" },
  { team: "Sample Team 03", r32: "84%", qf: "31%", final: "15%" },
  { team: "Sample Team 04", r32: "79%", qf: "28%", final: "12%" },
];

const groupRows = [
  { group: "Group A", favorite: "Sample Team 01", chaos: "Medium" },
  { group: "Group B", favorite: "Sample Team 05", chaos: "High" },
  { group: "Group C", favorite: "Sample Team 09", chaos: "Low" },
  { group: "Group D", favorite: "Sample Team 13", chaos: "Medium" },
];

export default function Home() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Tournament dashboard"
        title="World Cup simulation overview"
        description="Baseline probabilities, group outlooks, and scenario movement will appear here as the dashboard connects to the backend."
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Most likely winner"
          value="Sample Team 01"
          detail="14.2% champion probability"
          tone="green"
        />
        <MetricCard label="Simulations" value="1,000" detail="Poisson model" />
        <MetricCard label="Groups tracked" value="12" detail="48-team format" />
        <MetricCard
          label="Upset radar"
          value="6"
          detail="High-volatility fixtures"
          tone="amber"
        />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_1.2fr]">
        <section className="rounded-lg border border-zinc-200 bg-white p-5">
          <h2 className="text-base font-semibold text-zinc-950">
            Most likely winners
          </h2>
          <div className="mt-4 space-y-3">
            {winners.map((winner) => (
              <div
                key={winner.team}
                className="flex items-center justify-between gap-4 border-b border-zinc-100 pb-3 last:border-b-0 last:pb-0"
              >
                <span className="text-sm font-medium text-zinc-800">
                  {winner.team}
                </span>
                <span className="text-sm font-semibold text-emerald-700">
                  {winner.probability}
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-zinc-200 bg-white p-5">
          <h2 className="text-base font-semibold text-zinc-950">
            Champion probability table
          </h2>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase text-zinc-500">
                <tr>
                  <th className="py-2 font-semibold">Team</th>
                  <th className="py-2 font-semibold">Round of 32</th>
                  <th className="py-2 font-semibold">Quarter-final</th>
                  <th className="py-2 font-semibold">Final</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {stageRows.map((row) => (
                  <tr key={row.team}>
                    <td className="py-3 font-medium text-zinc-800">{row.team}</td>
                    <td className="py-3 text-zinc-600">{row.r32}</td>
                    <td className="py-3 text-zinc-600">{row.qf}</td>
                    <td className="py-3 text-zinc-600">{row.final}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-3">
        <section className="rounded-lg border border-zinc-200 bg-white p-5 xl:col-span-2">
          <h2 className="text-base font-semibold text-zinc-950">
            Group qualification overview
          </h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {groupRows.map((row) => (
              <div key={row.group} className="rounded-md border border-zinc-200 p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="font-semibold text-zinc-900">{row.group}</span>
                  <span className="rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-700">
                    {row.chaos}
                  </span>
                </div>
                <p className="mt-2 text-sm text-zinc-600">{row.favorite}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-lg border border-zinc-200 bg-white p-5">
          <h2 className="text-base font-semibold text-zinc-950">
            Biggest risers/fallers
          </h2>
          <div className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-3">
              <span className="text-zinc-700">Sample Team 12</span>
              <span className="font-semibold text-emerald-700">+4.1%</span>
            </div>
            <div className="flex justify-between gap-3">
              <span className="text-zinc-700">Sample Team 22</span>
              <span className="font-semibold text-rose-700">-3.5%</span>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

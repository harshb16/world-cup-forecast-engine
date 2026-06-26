import { SectionCard } from "@/components/ui/SectionCard";
import { DataFreshness } from "@/components/DataFreshness";
import { DataQualityReport } from "@/lib/api";
import { formatNumber } from "@/lib/format";

export function DataQualityDesk({ report }: { report: DataQualityReport }) {
  const warningTeams = report.teams.filter((team) => team.warnings.length > 0);

  return (
    <SectionCard>
      <p className="text-xs font-semibold uppercase text-signal-blue">
        Data quality desk
      </p>
      <h2 className="mt-1 text-lg font-semibold text-foreground">
        Source coverage and gaps
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        Last refresh <DataFreshness timestamp={report.last_refresh} />. All
        inputs are computed from open sources or flagged as missing.
      </p>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Object.entries(report.source_coverage).map(([key, value]) => (
          <div
            key={key}
            className="rounded-md border border-border bg-muted/40 px-3 py-3"
          >
            <p className="text-xs uppercase text-muted-foreground">
              {key.replaceAll("_", " ")}
            </p>
            <p className="mt-1 text-xl font-semibold text-foreground">
              {formatNumber(value)}
            </p>
          </div>
        ))}
      </div>

      {report.warnings.length > 0 ? (
        <div className="mt-5 rounded-md border border-[var(--score-amber)]/30 bg-[var(--score-amber)]/10 p-4">
          <h3 className="text-sm font-semibold text-signal-amber">
            Coverage warnings
          </h3>
          <ul className="mt-2 space-y-1 text-sm text-foreground">
            {report.warnings.map((warning) => (
              <li key={warning}>• {warning}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {warningTeams.length > 0 ? (
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-3 py-2">Team</th>
                <th className="px-3 py-2">Rating</th>
                <th className="px-3 py-2">Squad</th>
                <th className="px-3 py-2">Coverage</th>
                <th className="px-3 py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {warningTeams.slice(0, 8).map((team) => (
                <tr key={team.team_id} className="border-t border-border">
                  <td className="px-3 py-2 font-semibold text-foreground">
                    {team.team_name}
                  </td>
                  <td className="px-3 py-2">
                    {team.has_rating ? "Yes" : "Missing"}
                  </td>
                  <td className="px-3 py-2">
                    {team.has_squad_features ? "Yes" : "Missing"}
                  </td>
                  <td className="px-3 py-2">
                    {team.squad_coverage === null
                      ? "-"
                      : `${Math.round(team.squad_coverage * 100)}%`}
                  </td>
                  <td className="px-3 py-2 text-muted-foreground">
                    {team.warnings.join(" ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      <ul className="mt-5 space-y-2 text-sm leading-6 text-muted-foreground">
        {report.notes.map((note) => (
          <li key={note}>• {note}</li>
        ))}
      </ul>
    </SectionCard>
  );
}

"use client";

import { SectionCard } from "@/components/ui/SectionCard";
import { ThirdPlaceTracker } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import { THIRD_PLACE_QUALIFIER_COUNT, GROUP_WINNERS_AND_RUNNERS_UP } from "@/lib/tournament";

export function ThirdPlaceTrackerPanel({ tracker }: { tracker: ThirdPlaceTracker }) {
  return (
    <SectionCard>
      <p className="text-xs font-semibold uppercase text-primary">
        Third place
      </p>
      <h2 className="mt-1 text-lg font-semibold text-foreground">
        Best third-place bubble
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        The best {THIRD_PLACE_QUALIFIER_COUNT} third-place teams join the{" "}
        {GROUP_WINNERS_AND_RUNNERS_UP} group winners and runners-up in the Round
        of 32.
      </p>

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase text-muted-foreground">
            <tr>
              <th className="pb-3 pr-4">Group</th>
              <th className="pb-3 pr-4">Team</th>
              <th className="pb-3 pr-4">Qual%</th>
              <th className="pb-3 pr-4">Pts</th>
              <th className="pb-3">Avg sim pts</th>
            </tr>
          </thead>
          <tbody>
            {tracker.teams.map((team, index) => {
              const inBubble =
                index >= THIRD_PLACE_QUALIFIER_COUNT - 3 &&
                index <= THIRD_PLACE_QUALIFIER_COUNT + 2;
              const likelyQualifier = index < THIRD_PLACE_QUALIFIER_COUNT;
              return (
                <tr
                  key={team.team_id}
                  className={`border-t border-border ${
                    likelyQualifier ? "bg-emerald-400/5" : inBubble ? "bg-amber-400/5" : ""
                  }`}
                >
                  <td className="py-3 pr-4 font-mono text-muted-foreground">
                    {team.group_id}
                  </td>
                  <td className="py-3 pr-4 font-semibold text-foreground">
                    {team.team_name}
                    {likelyQualifier ? (
                      <span className="ml-2 rounded border border-emerald-400/30 bg-emerald-400/10 px-1.5 py-0.5 text-[0.65rem] uppercase text-primary">
                        Likely
                      </span>
                    ) : null}
                    {inBubble && !likelyQualifier ? (
                      <span className="ml-2 rounded border border-amber-400/30 bg-amber-400/10 px-1.5 py-0.5 text-[0.65rem] uppercase text-amber-200">
                        Bubble
                      </span>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4 text-primary">
                    {formatPercent(team.qualification_probability)}
                  </td>
                  <td className="py-3 pr-4 text-muted-foreground">
                    {team.current_points}
                  </td>
                  <td className="py-3 text-muted-foreground">
                    {team.simulated_average_points.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

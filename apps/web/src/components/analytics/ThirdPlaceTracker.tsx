"use client";

import { useEffect, useState } from "react";

import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import { SectionCard } from "@/components/ui/SectionCard";
import { fetchThirdPlaceTracker, ThirdPlaceTracker as ThirdPlaceData } from "@/lib/api";
import { formatPercent } from "@/lib/format";
import { THIRD_PLACE_QUALIFIER_COUNT, GROUP_WINNERS_AND_RUNNERS_UP } from "@/lib/tournament";
import { ANALYTICS_SIMULATION_COUNT } from "@/lib/config";

export function ThirdPlaceTrackerPanel() {
  const [data, setData] = useState<ThirdPlaceData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;
    fetchThirdPlaceTracker(undefined, ANALYTICS_SIMULATION_COUNT, 42)
      .then((tracker) => {
        if (isActive) {
          setData(tracker);
        }
      })
      .catch((caughtError: unknown) => {
        if (isActive) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : "Third-place tracker failed",
          );
        }
      });
    return () => {
      isActive = false;
    };
  }, []);

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return <LoadingState label="Loading third-place bubble" />;
  }

  return (
    <SectionCard>
      <p className="text-xs font-semibold uppercase text-[var(--turf)]">
        Third place
      </p>
      <h2 className="mt-1 text-lg font-semibold text-white">
        Best third-place bubble
      </h2>
      <p className="mt-1 text-sm text-zinc-400">
        The best {THIRD_PLACE_QUALIFIER_COUNT} third-place teams join the{" "}
        {GROUP_WINNERS_AND_RUNNERS_UP} group winners and runners-up in the Round
        of 32.
      </p>

      <div className="mt-5 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase text-zinc-500">
            <tr>
              <th className="pb-3 pr-4">Group</th>
              <th className="pb-3 pr-4">Team</th>
              <th className="pb-3 pr-4">Qual%</th>
              <th className="pb-3 pr-4">Pts</th>
              <th className="pb-3">Avg sim pts</th>
            </tr>
          </thead>
          <tbody>
            {data.teams.map((team, index) => {
              const inBubble =
                index >= THIRD_PLACE_QUALIFIER_COUNT - 3 &&
                index <= THIRD_PLACE_QUALIFIER_COUNT + 2;
              const likelyQualifier = index < THIRD_PLACE_QUALIFIER_COUNT;
              return (
                <tr
                  key={team.team_id}
                  className={`border-t border-white/10 ${
                    likelyQualifier ? "bg-emerald-400/5" : inBubble ? "bg-amber-400/5" : ""
                  }`}
                >
                  <td className="py-3 pr-4 font-mono text-zinc-400">
                    {team.group_id}
                  </td>
                  <td className="py-3 pr-4 font-semibold text-zinc-100">
                    {team.team_name}
                    {likelyQualifier ? (
                      <span className="ml-2 rounded border border-emerald-400/30 bg-emerald-400/10 px-1.5 py-0.5 text-[0.65rem] uppercase text-emerald-200">
                        Likely
                      </span>
                    ) : null}
                    {inBubble && !likelyQualifier ? (
                      <span className="ml-2 rounded border border-amber-400/30 bg-amber-400/10 px-1.5 py-0.5 text-[0.65rem] uppercase text-amber-200">
                        Bubble
                      </span>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4 text-emerald-200">
                    {formatPercent(team.qualification_probability)}
                  </td>
                  <td className="py-3 pr-4 text-zinc-300">
                    {team.current_points}
                  </td>
                  <td className="py-3 text-zinc-300">
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

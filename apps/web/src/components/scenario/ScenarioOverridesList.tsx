import { EmptyState } from "@/components/ui/EmptyState";
import { SectionCard } from "@/components/ui/SectionCard";
import { Match, MatchResultOverride, Team } from "@/lib/api";

export function ScenarioOverridesList({
  overrides,
  fixturesById,
  teamsById,
  onRemove,
  onClear,
}: {
  overrides: MatchResultOverride[];
  fixturesById: Map<string, Match>;
  teamsById: Map<string, Team>;
  onRemove: (matchId: string) => void;
  onClear: () => void;
}) {
  return (
    <SectionCard>
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase text-primary">
            Scenario slate
          </p>
          <h2 className="mt-1 text-lg font-semibold text-white">
            Selected overrides
          </h2>
        </div>
        <button
          type="button"
          onClick={onClear}
          className="rounded-md border border-border px-3 py-2 text-xs font-semibold text-zinc-300 transition hover:bg-white/[0.06]"
        >
          Clear
        </button>
      </div>
      <div className="mt-4 space-y-3">
        {overrides.length === 0 ? (
          <EmptyState
            title="No results selected yet"
            description="Add one or more match scores to compare the new tournament probabilities against the baseline."
          />
        ) : (
          overrides.map((override) => {
            const fixture = fixturesById.get(override.match_id);
            const teamA = fixture
              ? teamsById.get(fixture.team_a_id)?.name ?? fixture.team_a_id
              : "Team A";
            const teamB = fixture
              ? teamsById.get(fixture.team_b_id)?.name ?? fixture.team_b_id
              : "Team B";

            return (
              <div
                key={override.match_id}
                className="flex flex-col gap-3 rounded-md border border-border bg-white/[0.04] p-3 text-sm sm:flex-row sm:items-center sm:justify-between"
              >
                <span className="font-semibold text-zinc-100">
                  {teamA}{" "}
                  <span className="text-primary">
                    {override.team_a_goals} - {override.team_b_goals}
                  </span>{" "}
                  {teamB}
                </span>
                <button
                  type="button"
                  onClick={() => onRemove(override.match_id)}
                  className="self-start rounded-md border border-rose-300/20 px-2 py-1 text-xs font-semibold text-rose-200 transition hover:bg-rose-300/10 sm:self-auto"
                >
                  Remove
                </button>
              </div>
            );
          })
        )}
      </div>
    </SectionCard>
  );
}

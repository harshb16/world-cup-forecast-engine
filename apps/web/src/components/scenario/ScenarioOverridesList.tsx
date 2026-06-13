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
    <section className="rounded-lg border border-zinc-200 bg-white p-5">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-base font-semibold text-zinc-950">Overrides</h2>
        <button
          type="button"
          onClick={onClear}
          className="rounded-md border border-zinc-300 px-3 py-2 text-xs font-semibold text-zinc-700 transition hover:bg-zinc-100"
        >
          Clear
        </button>
      </div>
      <div className="mt-4 space-y-3">
        {overrides.length === 0 ? (
          <p className="text-sm text-zinc-500">No overrides added.</p>
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
                className="flex items-center justify-between gap-4 rounded-md border border-zinc-100 p-3 text-sm"
              >
                <span className="text-zinc-700">
                  {teamA} {override.team_a_goals} - {override.team_b_goals}{" "}
                  {teamB}
                </span>
                <button
                  type="button"
                  onClick={() => onRemove(override.match_id)}
                  className="text-xs font-semibold text-rose-700"
                >
                  Remove
                </button>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}

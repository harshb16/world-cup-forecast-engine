import { SectionCard } from "@/components/ui/SectionCard";
import { DataMetadata } from "@/lib/api";
import { formatNumber } from "@/lib/format";

export function DataStatusCard({ metadata }: { metadata: DataMetadata }) {
  return (
    <SectionCard>
      <div className="grid gap-3 md:grid-cols-4">
        <Status label="Status" value={metadata.is_real_data ? "Real World Cup Data" : "Sample Data"} />
        <Status label="Rating source" value={metadata.rating_source ?? "Unknown"} />
        <Status label="Last updated" value={metadata.last_updated ?? "Unknown"} />
        <Status label="Bracket" value={metadata.bracket_status ?? "Unknown"} />
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-5">
        <Status label="Teams" value={formatNumber(metadata.team_count)} />
        <Status label="Groups" value={formatNumber(metadata.group_count)} />
        <Status label="Fixtures" value={formatNumber(metadata.fixture_count)} />
        <Status
          label="Results"
          value={formatNumber(metadata.completed_result_count)}
        />
        <Status
          label="Ratings"
          value={`${formatNumber(metadata.rating_coverage_count)}/${formatNumber(metadata.team_count)}`}
        />
      </div>
      {!metadata.ratings_are_official ? (
        <p className="mt-3 text-xs leading-5 text-zinc-400">
          Ratings are external or derived, not official FIFA strength ratings.
        </p>
      ) : null}
      {metadata.model_limitations.length > 0 ? (
        <p className="mt-2 text-xs leading-5 text-zinc-400">
          {metadata.model_limitations[0]}
        </p>
      ) : null}
    </SectionCard>
  );
}

function Status({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase text-zinc-500">{label}</p>
      <p className="mt-1 text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

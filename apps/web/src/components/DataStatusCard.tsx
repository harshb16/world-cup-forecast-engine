import { DataMetadata } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import { DataFreshness } from "@/components/DataFreshness";

export function DataStatusCard({ metadata }: { metadata: DataMetadata }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border border-border bg-card/85 px-4 py-3 text-sm">
      <StatusChip
        label="Version"
        value={metadata.data_version ?? "Unknown"}
      />
      <span className="text-zinc-400">
        <span className="mr-1 text-xs uppercase text-zinc-500">Data</span>
        <DataFreshness timestamp={metadata.last_updated} />
      </span>
      <StatusChip
        label="Results"
        value={formatNumber(metadata.completed_result_count)}
      />
      <StatusChip
        label="Source"
        value={metadata.result_source ?? "Published snapshot"}
      />
    </div>
  );
}

function StatusChip({ label, value }: { label: string; value: string }) {
  return (
    <span className="text-zinc-400">
      <span className="mr-1 text-xs uppercase text-zinc-500">{label}</span>
      <span className="font-semibold text-zinc-100">{value}</span>
    </span>
  );
}

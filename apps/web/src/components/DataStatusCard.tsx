import { DataMetadata } from "@/lib/api";
import { formatNumber } from "@/lib/format";

export function DataStatusCard({ metadata }: { metadata: DataMetadata }) {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border border-white/10 bg-[#101722]/85 px-4 py-3 text-sm">
      <StatusChip
        label="Version"
        value={metadata.data_version ?? "Unknown"}
      />
      <StatusChip
        label="Updated"
        value={metadata.last_updated ?? "Unknown"}
      />
      <StatusChip
        label="Results"
        value={formatNumber(metadata.completed_result_count)}
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

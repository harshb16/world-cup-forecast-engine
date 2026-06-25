"use client";

import { RefreshCw } from "lucide-react";

export function ForecastRefreshControl({
  isRefreshing,
  lastRunAt,
  onRefresh,
}: {
  isRefreshing: boolean;
  lastRunAt: Date | null;
  onRefresh: () => Promise<void>;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => void onRefresh()}
        disabled={isRefreshing}
        className="inline-flex items-center gap-2 rounded-md border border-white/15 bg-white/[0.05] px-3 py-2 text-sm font-semibold text-white transition hover:bg-white/[0.09] disabled:cursor-wait disabled:text-zinc-500"
      >
        <RefreshCw
          size={15}
          aria-hidden="true"
          className={isRefreshing ? "animate-spin" : ""}
        />
        {isRefreshing ? "Rerunning simulation" : "Rerun simulation"}
      </button>
      <span
        aria-live="polite"
        className="font-mono text-[0.65rem] uppercase tracking-[0.1em] text-zinc-500"
      >
        {lastRunAt
          ? `Using loaded match data · ran ${lastRunAt.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}`
          : "Uses loaded match data · does not sync results"}
      </span>
    </div>
  );
}

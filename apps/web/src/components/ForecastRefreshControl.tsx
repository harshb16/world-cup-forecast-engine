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
        className="inline-flex items-center gap-2 rounded-md border border-border bg-accent/50 px-3 py-2 text-sm font-semibold text-foreground transition hover:bg-white/[0.09] disabled:cursor-wait disabled:text-muted-foreground"
      >
        <RefreshCw
          size={15}
          aria-hidden="true"
          className={isRefreshing ? "animate-spin" : ""}
        />
        {isRefreshing ? "Refreshing view" : "Refresh view"}
      </button>
      <span
        aria-live="polite"
        className="font-mono text-[0.65rem] uppercase tracking-[0.1em] text-muted-foreground"
      >
        {lastRunAt
          ? `Published forecast · loaded ${lastRunAt.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}`
          : "Published forecast · polls for updates"}
      </span>
    </div>
  );
}

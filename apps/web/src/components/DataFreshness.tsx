"use client";

import { useEffect, useState } from "react";

import { getDataFreshness } from "@/lib/freshness";

const levelStyles = {
  current: "text-[var(--turf)]",
  delayed: "text-[var(--score-amber)]",
  stale: "text-[var(--risk-red)]",
  unknown: "text-zinc-400",
} as const;

const levelLabels = {
  current: "Current",
  delayed: "Delayed",
  stale: "Stale",
  unknown: "Unknown",
} as const;

export function DataFreshness({
  timestamp,
  compact = false,
}: {
  timestamp: string | null | undefined;
  compact?: boolean;
}) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const interval = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(interval);
  }, []);

  const freshness = getDataFreshness(timestamp, now);

  if (compact) {
    return (
      <span
        className={levelStyles[freshness.level]}
        title={freshness.exact}
        suppressHydrationWarning
      >
        {levelLabels[freshness.level]} · {freshness.relative}
      </span>
    );
  }

  return (
    <span title={freshness.exact} suppressHydrationWarning>
      <span className={`font-semibold ${levelStyles[freshness.level]}`}>
        {levelLabels[freshness.level]}
      </span>
      <span className="ml-1 font-semibold text-zinc-100">
        {freshness.relative}
      </span>
      <span className="ml-2 text-xs text-zinc-500">({freshness.exact})</span>
    </span>
  );
}

export type FreshnessLevel = "current" | "delayed" | "stale" | "unknown";

export type DataFreshness = {
  exact: string;
  level: FreshnessLevel;
  relative: string;
};

const DELAYED_AFTER_HOURS = 12;
const STALE_AFTER_HOURS = 24;

export function getDataFreshness(
  timestamp: string | null | undefined,
  now = new Date(),
): DataFreshness {
  if (!timestamp) {
    return {
      exact: "Update time unavailable",
      level: "unknown",
      relative: "Unknown",
    };
  }

  const updatedAt = new Date(timestamp);
  if (Number.isNaN(updatedAt.getTime())) {
    return {
      exact: "Invalid update timestamp",
      level: "unknown",
      relative: "Unknown",
    };
  }

  const exact = new Intl.DateTimeFormat("en-US", {
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    month: "short",
    timeZone: "UTC",
    timeZoneName: "short",
    year: "numeric",
  }).format(updatedAt);
  const ageMs = now.getTime() - updatedAt.getTime();
  const ageHours = ageMs / 3_600_000;

  if (ageMs < -300_000) {
    return {
      exact,
      level: "unknown",
      relative: "Timestamp is in the future",
    };
  }

  const level: FreshnessLevel =
    ageHours > STALE_AFTER_HOURS
      ? "stale"
      : ageHours > DELAYED_AFTER_HOURS
        ? "delayed"
        : "current";

  return {
    exact,
    level,
    relative: formatRelativeAge(Math.max(ageMs, 0)),
  };
}

function formatRelativeAge(ageMs: number): string {
  const minutes = Math.floor(ageMs / 60_000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours} hr ago`;

  const days = Math.floor(hours / 24);
  return `${days} days ago`;
}

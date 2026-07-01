const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

function boundedInteger(
  value: string | undefined,
  fallback: number,
  minimum: number,
): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= minimum ? parsed : fallback;
}

export const SIMULATION_COUNT = boundedInteger(
  process.env.NEXT_PUBLIC_WCO_SIMULATIONS,
  1000,
  1000,
);

export const ANALYTICS_SIMULATION_COUNT = boundedInteger(
  process.env.NEXT_PUBLIC_WCO_ANALYTICS_SIMULATIONS,
  500,
  100,
);

export const TEAM_PATH_SIMULATION_COUNT = boundedInteger(
  process.env.NEXT_PUBLIC_WCO_TEAM_PATH_SIMULATIONS,
  500,
  100,
);
// Used only for optional live POST /team-path diagnostics; default UI uses GET.

export const ADMIN_UI_ENABLED =
  process.env.NEXT_PUBLIC_WCO_ADMIN_UI === "true";

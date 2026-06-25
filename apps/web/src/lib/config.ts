const DEFAULT_API_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

const FAST_TEST_MODE = process.env.NEXT_PUBLIC_WCO_FAST_MODE === "1";

function positiveInteger(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

export const SIMULATION_COUNT = positiveInteger(
  process.env.NEXT_PUBLIC_WCO_SIMULATIONS,
  FAST_TEST_MODE ? 20 : 1000,
);

export const ANALYTICS_SIMULATION_COUNT = positiveInteger(
  process.env.NEXT_PUBLIC_WCO_ANALYTICS_SIMULATIONS,
  FAST_TEST_MODE ? 10 : 500,
);

export const TEAM_PATH_SIMULATION_COUNT = positiveInteger(
  process.env.NEXT_PUBLIC_WCO_TEAM_PATH_SIMULATIONS,
  FAST_TEST_MODE ? 10 : 500,
);

export const FORECAST_REFRESH_INTERVAL_MS =
  positiveInteger(process.env.NEXT_PUBLIC_WCO_REFRESH_MINUTES, 5) * 60_000;

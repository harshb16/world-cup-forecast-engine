"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { FORECAST_REFRESH_INTERVAL_MS } from "@/lib/config";

type AutoForecastOptions = {
  intervalMs?: number;
};

type AutoForecastState<T> = {
  data: T | null;
  error: string | null;
  isRefreshing: boolean;
  lastRunAt: Date | null;
  clear: () => void;
  refresh: () => Promise<void>;
};

export function useAutoForecast<T>(
  loader: () => Promise<T>,
  { intervalMs = FORECAST_REFRESH_INTERVAL_MS }: AutoForecastOptions = {},
): AutoForecastState<T> {
  const loaderRef = useRef(loader);
  const requestIdRef = useRef(0);
  const lastRunRef = useRef<Date | null>(null);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRunAt, setLastRunAt] = useState<Date | null>(null);

  const run = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setIsRefreshing(true);
    setError(null);

    try {
      const nextData = await loaderRef.current();
      if (requestId !== requestIdRef.current) return;

      const completedAt = new Date();
      setData(nextData);
      setLastRunAt(completedAt);
      lastRunRef.current = completedAt;
    } catch (caught: unknown) {
      if (requestId !== requestIdRef.current) return;
      setError(
        caught instanceof Error ? caught.message : "Forecast refresh failed",
      );
    } finally {
      if (requestId === requestIdRef.current) {
        setIsRefreshing(false);
      }
    }
  }, []);

  const clear = useCallback(() => {
    requestIdRef.current += 1;
    setData(null);
    setError(null);
    setIsRefreshing(false);
  }, []);

  useEffect(() => {
    loaderRef.current = loader;
    const initialRefresh = window.setTimeout(() => void run(), 0);
    return () => {
      window.clearTimeout(initialRefresh);
      requestIdRef.current += 1;
    };
  }, [loader, run]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (document.visibilityState === "visible") void run();
    }, intervalMs);

    function refreshAfterReturning() {
      const lastRun = lastRunRef.current;
      if (
        document.visibilityState === "visible" &&
        (!lastRun || Date.now() - lastRun.getTime() >= intervalMs)
      ) {
        void run();
      }
    }

    document.addEventListener("visibilitychange", refreshAfterReturning);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", refreshAfterReturning);
    };
  }, [intervalMs, run]);

  return {
    data,
    error,
    isRefreshing,
    lastRunAt,
    clear,
    refresh: run,
  };
}

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

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
): AutoForecastState<T> {
  const loaderRef = useRef(loader);
  const requestIdRef = useRef(0);
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

  return {
    data,
    error,
    isRefreshing,
    lastRunAt,
    clear,
    refresh: run,
  };
}

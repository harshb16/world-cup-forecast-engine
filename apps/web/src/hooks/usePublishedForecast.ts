"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { fetchForecastStatus } from "@/lib/api";

const DEFAULT_POLL_INTERVAL_MS = 30_000;

type PublishedForecastState<T> = {
  data: T | null;
  error: string | null;
  isRefreshing: boolean;
  lastRunAt: Date | null;
  snapshotId: string | null;
  clear: () => void;
  refresh: () => Promise<void>;
};

export function usePublishedForecast<T>(
  loader: () => Promise<T>,
  pollIntervalMs: number = DEFAULT_POLL_INTERVAL_MS,
): PublishedForecastState<T> {
  const loaderRef = useRef(loader);
  const requestIdRef = useRef(0);
  const snapshotIdRef = useRef<string | null>(null);
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRunAt, setLastRunAt] = useState<Date | null>(null);
  const [snapshotId, setSnapshotId] = useState<string | null>(null);

  const syncSnapshotId = useCallback(async () => {
    const status = await fetchForecastStatus();
    snapshotIdRef.current = status.snapshot_id;
    setSnapshotId(status.snapshot_id);
    return status.snapshot_id;
  }, []);

  const run = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    setIsRefreshing(true);
    setError(null);

    try {
      const nextData = await loaderRef.current();
      if (requestId !== requestIdRef.current) return;

      await syncSnapshotId();
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
  }, [syncSnapshotId]);

  const clear = useCallback(() => {
    requestIdRef.current += 1;
    snapshotIdRef.current = null;
    setSnapshotId(null);
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
    let cancelled = false;

    const poll = async () => {
      try {
        const status = await fetchForecastStatus();
        if (cancelled) return;

        if (
          snapshotIdRef.current !== null &&
          status.snapshot_id !== snapshotIdRef.current
        ) {
          snapshotIdRef.current = status.snapshot_id;
          setSnapshotId(status.snapshot_id);
          await run();
          return;
        }

        snapshotIdRef.current = status.snapshot_id;
        setSnapshotId(status.snapshot_id);
      } catch {
        // Ignore transient polling failures; keep showing the last snapshot.
      }
    };

    const intervalId = window.setInterval(() => void poll(), pollIntervalMs);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [pollIntervalMs, run]);

  return {
    data,
    error,
    isRefreshing,
    lastRunAt,
    snapshotId,
    clear,
    refresh: run,
  };
}

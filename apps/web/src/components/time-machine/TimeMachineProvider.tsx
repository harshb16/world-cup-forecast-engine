"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

import {
  fetchTimeMachineManifest,
  fetchTimeMachineSnapshot,
  fetchTimeMachineTeamPath,
  TimeMachineManifest,
  TimeMachineSnapshot,
  TeamPath,
} from "@/lib/api";

const SUPPORTED_PATHS = ["/", "/dashboard", "/groups", "/bracket", "/teams", "/time-machine"];

type TimeMachineContextValue = {
  isReplay: boolean;
  manifest: TimeMachineManifest | null;
  snapshot: TimeMachineSnapshot | null;
  milestoneId: string | null;
  loading: boolean;
  error: string | null;
  statusMessage: string | null;
  selectMilestone: (id: string) => void;
  hrefFor: (href: string) => string;
  loadTeamPath: (teamId: string) => Promise<TeamPath>;
};

const TimeMachineContext = createContext<TimeMachineContextValue | null>(null);

function supportsReplay(pathname: string): boolean {
  return SUPPORTED_PATHS.some(
    (path) => pathname === path || (path === "/teams" && pathname.startsWith("/teams/")),
  );
}

export function TimeMachineProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const requestedId = searchParams.get("at");
  const isReplay = Boolean(requestedId && supportsReplay(pathname));
  const [manifest, setManifest] = useState<TimeMachineManifest | null>(null);
  const [snapshot, setSnapshot] = useState<TimeMachineSnapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const snapshotCache = useRef(new Map<string, TimeMachineSnapshot>());
  const pathCache = useRef(new Map<string, TeamPath>());
  const activeSnapshot = snapshot?.milestone.id === requestedId ? snapshot : null;

  const replaceMilestone = useCallback(
    (id: string, preserveStatus = false) => {
      if (!preserveStatus) setStatusMessage(null);
      const query = new URLSearchParams(searchParams.toString());
      query.set("at", id);
      router.replace(`${pathname}?${query.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  useEffect(() => {
    if (!requestedId || !supportsReplay(pathname)) {
      return;
    }
    let active = true;
    const load = async () => {
      const catalog = manifest ?? (await fetchTimeMachineManifest());
      if (!active) return;
      setManifest(catalog);
      const requestedIndex = catalog.milestones.findIndex((item) => item.id === requestedId);
      const candidates = catalog.milestones.filter(
        (item) => item.available && (requestedIndex < 0 || item.order <= requestedIndex),
      );
      const selected =
        catalog.milestones.find((item) => item.id === requestedId && item.available) ??
        candidates.at(-1) ??
        catalog.milestones.find((item) => item.available);
      if (!selected) throw new Error("No replay milestones are available.");
      if (selected.id !== requestedId) {
        setStatusMessage(`Replay corrected to ${selected.label}, the closest available milestone.`);
        replaceMilestone(selected.id, true);
      }
      const cached = snapshotCache.current.get(selected.id);
      const loaded = cached ?? (await fetchTimeMachineSnapshot(selected.id));
      snapshotCache.current.set(selected.id, loaded);
      if (!active) return;
      setError(null);
      setSnapshot(loaded);
      const adjacent = [selected.previous_id, selected.next_id].filter(Boolean) as string[];
      void Promise.all(
        adjacent.map(async (id) => {
          const item = catalog.milestones.find((candidate) => candidate.id === id);
          if (!item?.available || snapshotCache.current.has(id)) return;
          snapshotCache.current.set(id, await fetchTimeMachineSnapshot(id));
        }),
      ).catch(() => undefined);
    };
    load()
      .catch((caught: unknown) => {
        if (active) setError(caught instanceof Error ? caught.message : "Replay failed to load.");
      })
    return () => {
      active = false;
    };
  }, [manifest, pathname, replaceMilestone, requestedId]);

  const hrefFor = useCallback(
    (href: string) => {
      const url = new URL(href, "https://local.invalid");
      const query = new URLSearchParams(url.search);
      if (requestedId && supportsReplay(url.pathname)) query.set("at", requestedId);
      else query.delete("at");
      return `${url.pathname}${query.size ? `?${query}` : ""}${url.hash}`;
    },
    [requestedId],
  );

  const loadTeamPath = useCallback(
    async (teamId: string) => {
      if (!activeSnapshot) throw new Error("Select a replay milestone first.");
      const key = `${activeSnapshot.milestone.id}:${teamId}`;
      const cached = pathCache.current.get(key);
      if (cached) return cached;
      const path = await fetchTimeMachineTeamPath(activeSnapshot.milestone.id, teamId);
      pathCache.current.set(key, path);
      return path;
    },
    [activeSnapshot],
  );

  const value = useMemo<TimeMachineContextValue>(
    () => ({
      isReplay,
      manifest,
      snapshot: activeSnapshot,
      milestoneId: activeSnapshot?.milestone.id ?? requestedId,
      loading: isReplay && !activeSnapshot && !error,
      error,
      statusMessage,
      selectMilestone: replaceMilestone,
      hrefFor,
      loadTeamPath,
    }),
    [activeSnapshot, error, hrefFor, isReplay, loadTeamPath, manifest, replaceMilestone, requestedId, statusMessage],
  );

  return <TimeMachineContext.Provider value={value}>{children}</TimeMachineContext.Provider>;
}

export function useTimeMachine(): TimeMachineContextValue {
  const value = useContext(TimeMachineContext);
  if (!value) throw new Error("useTimeMachine must be used within TimeMachineProvider");
  return value;
}

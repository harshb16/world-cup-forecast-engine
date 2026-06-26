"use client";

import { useState } from "react";
import { DatabaseZap } from "lucide-react";

import { syncMatchResults, type SyncJobDetail } from "@/lib/api";

const ADMIN_KEY_STORAGE = "wco-admin-sync-key";

function formatStage(job: SyncJobDetail | null): string | null {
  if (!job) {
    return null;
  }
  if (job.status === "succeeded") {
    return `${job.completed_result_count ?? 0} results · ${job.changed_fixture_count ?? 0} changed · ${job.provider ?? "provider"}`;
  }
  if (job.status === "failed") {
    return job.errors[0] ?? "Sync failed";
  }
  return job.stage.replaceAll("_", " ");
}

export function SyncResultsControl({
  onSynced,
}: {
  onSynced: () => Promise<void>;
}) {
  const [isSyncing, setIsSyncing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function syncResults() {
    const storedKey = window.sessionStorage.getItem(ADMIN_KEY_STORAGE);
    const adminKey =
      storedKey ??
      window.prompt(
        "Enter the admin sync key. It stays in this browser tab only.",
      );
    if (!adminKey) {
      return;
    }

    window.sessionStorage.setItem(ADMIN_KEY_STORAGE, adminKey);
    setIsSyncing(true);
    setMessage("queued");
    try {
      const result = await syncMatchResults(adminKey, (job) => {
        setMessage(formatStage(job));
      });
      setMessage(
        `${result.completed_result_count ?? 0} results · ${result.changed_fixture_count} changed · ${result.provider ?? "provider"}`,
      );
      await onSynced();
    } catch (caught: unknown) {
      const error =
        caught instanceof Error ? caught.message : "Result sync failed.";
      if (error.toLowerCase().includes("key")) {
        window.sessionStorage.removeItem(ADMIN_KEY_STORAGE);
      }
      setMessage(error);
    } finally {
      setIsSyncing(false);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => void syncResults()}
        disabled={isSyncing}
        className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-semibold text-primary-foreground transition hover:brightness-110 disabled:cursor-wait disabled:opacity-60"
      >
        <DatabaseZap
          size={15}
          aria-hidden="true"
          className={isSyncing ? "animate-pulse" : ""}
        />
        {isSyncing ? "Syncing results" : "Sync match results"}
      </button>
      {message ? (
        <span
          role="status"
          className="max-w-lg font-mono text-[0.65rem] uppercase tracking-[0.08em] text-muted-foreground"
        >
          {message}
        </span>
      ) : null}
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Braces,
  Database,
  GitBranch,
  Scale,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

import { DataFreshness } from "@/components/DataFreshness";
import { ErrorState } from "@/components/ErrorState";
import { LoadingState } from "@/components/LoadingState";
import {
  CurrentTournamentScoring,
  DataMetadata,
  DEFAULT_MODEL_TYPE,
  fetchCurrentTournamentScoring,
  fetchMetadata,
  fetchModelMetadata,
  ModelMetadata,
} from "@/lib/api";
import { formatModelLabel, formatNumber, formatPercent } from "@/lib/format";

type MethodologyData = {
  metadata: DataMetadata;
  models: ModelMetadata[];
  scoring: CurrentTournamentScoring;
};

type PipelineSection = {
  id: string;
  number: string;
  eyebrow: string;
  title: string;
  summary: string;
  icon: LucideIcon;
};

const pipeline: PipelineSection[] = [
  {
    id: "data",
    number: "01",
    eyebrow: "Inputs",
    title: "Start with auditable tournament data",
    summary:
      "Teams, groups, fixtures, completed results, ratings, and model parameters are stored as versioned processed files. Missing coverage is surfaced rather than silently invented.",
    icon: Database,
  },
  {
    id: "strength",
    number: "02",
    eyebrow: "Team strength",
    title: "Update an Elo rating from senior internationals",
    summary:
      "The production model uses open international results from 2018 onward. Match importance is represented by a fixed K-factor, non-neutral games include home advantage, and score margin scales each update.",
    icon: Scale,
  },
  {
    id: "matches",
    number: "03",
    eyebrow: "Match probabilities",
    title: "Turn rating gaps into win, draw, and loss chances",
    summary:
      "An Elo curve estimates the decisive-result share. Draw probability starts at 26%, shrinks for large rating gaps, and never falls below 12%. The production model does not claim direct xG or player-level inputs.",
    icon: Braces,
  },
  {
    id: "tournament",
    number: "04",
    eyebrow: "Tournament engine",
    title: "Replay every unresolved path",
    summary:
      "Played matches stay fixed. Remaining group and knockout matches are sampled, twelve group tables are rebuilt, eight third-place teams qualify, and the published Round-of-32 slot structure carries winners through the final.",
    icon: GitBranch,
  },
  {
    id: "evaluation",
    number: "05",
    eyebrow: "Evaluation",
    title: "Score today’s model without overselling it",
    summary:
      "Accuracy, multiclass Brier score, log loss, and confidence buckets are calculated against completed matches in the active tournament. This is current-tournament scoring—not historical out-of-sample proof.",
    icon: BarChart3,
  },
  {
    id: "limits",
    number: "06",
    eyebrow: "Boundaries",
    title: "Name what the forecast cannot know",
    summary:
      "No private injury feed, confirmed lineups, direct international xG, betting market, travel model, or tactical event data is used. Small simulation probabilities also carry sampling noise.",
    icon: AlertTriangle,
  },
];

export function MethodologyExperience() {
  const [data, setData] = useState<MethodologyData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      fetchMetadata(),
      fetchModelMetadata(),
      fetchCurrentTournamentScoring(DEFAULT_MODEL_TYPE),
    ])
      .then(([metadata, models, scoring]) => {
        if (active) setData({ metadata, models, scoring });
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Methodology data request failed",
          );
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const productionModel = useMemo(
    () => data?.models.find((model) => model.id === DEFAULT_MODEL_TYPE) ?? null,
    [data],
  );

  if (error) return <ErrorState message={error} />;
  if (!data || !productionModel) {
    return <LoadingState label="Loading methodology" />;
  }

  return (
    <div className="space-y-10 pb-16">
      <header className="relative overflow-hidden rounded-xl border border-white/10 bg-[#0a1118] px-6 py-8 sm:px-9 sm:py-10">
        <div
          className="pointer-events-none absolute inset-y-0 right-0 w-2/5 opacity-40"
          aria-hidden="true"
          style={{
            background:
              "repeating-linear-gradient(135deg, transparent 0 18px, rgba(47,209,124,.13) 18px 19px)",
          }}
        />
        <div className="relative max-w-4xl">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-[var(--turf)]">
            Public methodology · model {productionModel.id}
          </p>
          <h1 className="mt-4 text-4xl font-semibold leading-[1.05] tracking-[-0.035em] text-white sm:text-6xl">
            Every percentage should have a paper trail.
          </h1>
          <p className="mt-5 max-w-3xl text-base leading-7 text-zinc-300 sm:text-lg">
            World Cup Oracle converts open match history into team ratings,
            match probabilities, and thousands of complete tournament paths.
            This page shows what happens at each step—and where confidence
            should stop.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link
              href="/"
              className="inline-flex items-center gap-2 rounded-md bg-[var(--turf)] px-4 py-2.5 text-sm font-semibold text-zinc-950 transition hover:brightness-110"
            >
              Open forecast <ArrowRight size={16} aria-hidden="true" />
            </Link>
            <Link
              href="/models"
              className="inline-flex items-center gap-2 rounded-md border border-white/15 bg-white/[0.05] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/[0.09]"
            >
              Inspect models
            </Link>
          </div>
        </div>
      </header>

      <section
        aria-label="Current methodology status"
        className="grid overflow-hidden rounded-xl border border-white/10 bg-[#0b1118] sm:grid-cols-2 xl:grid-cols-4"
      >
        <StatusCell
          label="Production model"
          value={formatModelLabel(DEFAULT_MODEL_TYPE)}
          detail="Open-data rating baseline"
        />
        <StatusCell
          label="Tournament data"
          value={`${data.metadata.team_count} teams`}
          detail={`${data.metadata.group_count} groups · ${data.metadata.fixture_count} fixtures`}
        />
        <StatusCell
          label="Known results"
          value={formatNumber(data.metadata.completed_result_count)}
          detail="Fixed in every simulation"
        />
        <div className="border-white/10 p-5 sm:border-l">
          <p className="font-mono text-[0.68rem] uppercase tracking-[0.14em] text-zinc-500">
            Data freshness
          </p>
          <p className="mt-2 text-lg">
            <DataFreshness timestamp={data.metadata.last_updated} compact />
          </p>
          <p className="mt-1 truncate text-xs text-zinc-500">
            {data.metadata.data_version ?? "Version unavailable"}
          </p>
        </div>
      </section>

      <div className="grid gap-8 xl:grid-cols-[15rem_minmax(0,1fr)]">
        <aside className="hidden xl:block">
          <nav
            aria-label="Methodology sections"
            className="sticky top-6 rounded-xl border border-white/10 bg-[#0b1118] p-3"
          >
            {pipeline.map((section) => (
              <a
                key={section.id}
                href={`#${section.id}`}
                className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm text-zinc-400 transition hover:bg-white/[0.05] hover:text-white"
              >
                <span className="font-mono text-xs text-[var(--turf)]">
                  {section.number}
                </span>
                {section.eyebrow}
              </a>
            ))}
          </nav>
        </aside>

        <main className="relative min-w-0">
          <div
            className="absolute bottom-8 left-[1.45rem] top-8 w-px bg-gradient-to-b from-[var(--turf)] via-[var(--var-blue)] to-[var(--score-amber)] opacity-40 sm:left-[2.2rem]"
            aria-hidden="true"
          />
          <div className="space-y-6">
            {pipeline.map((section) => (
              <MethodSection
                key={section.id}
                section={section}
                data={data}
                productionModel={productionModel}
              />
            ))}
          </div>
        </main>
      </div>

      <section className="rounded-xl border border-[var(--turf)]/25 bg-[var(--turf)]/[0.06] p-6 sm:p-8">
        <div className="flex items-start gap-4">
          <ShieldCheck
            size={26}
            className="mt-1 shrink-0 text-[var(--turf)]"
            aria-hidden="true"
          />
          <div>
            <h2 className="text-xl font-semibold text-white">
              What a probability means here
            </h2>
            <p className="mt-2 max-w-4xl text-sm leading-6 text-zinc-300">
              A 20% title chance means the team won about one in five simulated
              tournaments under this model, these inputs, and the current known
              results. It does not mean the outcome is certain, official, or
              immune to injuries, lineup changes, and new information.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

function MethodSection({
  section,
  data,
  productionModel,
}: {
  section: PipelineSection;
  data: MethodologyData;
  productionModel: ModelMetadata;
}) {
  const Icon = section.icon;

  return (
    <section
      id={section.id}
      className="scroll-mt-6 rounded-xl border border-white/10 bg-[#0b1118] p-5 sm:p-7"
    >
      <div className="grid gap-5 sm:grid-cols-[4.5rem_minmax(0,1fr)]">
        <div className="relative z-10 flex size-12 items-center justify-center rounded-full border border-white/15 bg-[#101722] font-mono text-xs font-semibold text-[var(--turf)] sm:size-[4.5rem]">
          <Icon size={22} aria-hidden="true" />
          <span className="sr-only">Step {section.number}</span>
        </div>
        <div className="min-w-0">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
            {section.number} · {section.eyebrow}
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-[-0.02em] text-white sm:text-3xl">
            {section.title}
          </h2>
          <p className="mt-3 max-w-4xl text-sm leading-7 text-zinc-300">
            {section.summary}
          </p>
          <SectionEvidence
            id={section.id}
            data={data}
            productionModel={productionModel}
          />
        </div>
      </div>
    </section>
  );
}

function SectionEvidence({
  id,
  data,
  productionModel,
}: {
  id: string;
  data: MethodologyData;
  productionModel: ModelMetadata;
}) {
  if (id === "data") {
    const sources = data.metadata.sources
      .map(normalizeSource)
      .filter((source): source is MethodologySource => source !== null);
    return (
      <div className="mt-6 grid gap-3 md:grid-cols-2">
        {sources.map((source) => (
          <a
            key={`${source.name}-${source.url}`}
            href={source.url}
            target="_blank"
            rel="noreferrer"
            className="rounded-lg border border-white/10 bg-black/20 p-4 transition hover:border-[var(--var-blue)]/40 hover:bg-white/[0.04]"
          >
            <p className="font-semibold text-white">{source.name}</p>
            <p className="mt-1 text-xs leading-5 text-zinc-400">
              {source.usage}
            </p>
          </a>
        ))}
      </div>
    );
  }

  if (id === "strength") {
    return (
      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        <Evidence label="Base rating" value="1500" />
        <Evidence label="K-factor" value="28" />
        <Evidence label="Home advantage" value="55 Elo" />
        <Evidence label="Goal margin" value="Square-root scaling" />
      </div>
    );
  }

  if (id === "matches") {
    return (
      <div className="mt-6 rounded-lg border border-white/10 bg-black/25 p-4 font-mono text-xs leading-6 text-zinc-300 sm:text-sm">
        <p>
          expected(A) = 1 / (1 + 10
          <sup>−(rating A − rating B) / 400</sup>)
        </p>
        <p className="mt-2 text-zinc-500">
          Decisive probability is split using this expectation after reserving
          the modelled draw share.
        </p>
      </div>
    );
  }

  if (id === "tournament") {
    return (
      <ol className="mt-6 grid gap-3 md:grid-cols-2">
        {[
          "Keep completed match scores unchanged.",
          "Sample every remaining group match.",
          "Rank groups by points, goal difference, goals, then team ID.",
          "Advance top two plus eight best third-place teams.",
          "Place qualifiers into the 2026 Round-of-32 slot structure.",
          "Play knockout rounds through extra-time/penalty resolution.",
        ].map((item, index) => (
          <li
            key={item}
            className="flex gap-3 rounded-lg border border-white/10 bg-black/20 p-4 text-sm leading-6 text-zinc-300"
          >
            <span className="font-mono text-xs text-[var(--var-blue)]">
              {String(index + 1).padStart(2, "0")}
            </span>
            {item}
          </li>
        ))}
      </ol>
    );
  }

  if (id === "evaluation") {
    return (
      <div className="mt-6">
        <div className="grid gap-3 sm:grid-cols-3">
          <Evidence
            label="Accuracy"
            value={
              data.scoring.accuracy === null
                ? "Unavailable"
                : formatPercent(data.scoring.accuracy)
            }
          />
          <Evidence
            label="Brier score"
            value={
              data.scoring.brier_score === null
                ? "Unavailable"
                : data.scoring.brier_score.toFixed(3)
            }
          />
          <Evidence
            label="Log loss"
            value={
              data.scoring.log_loss === null
                ? "Unavailable"
                : data.scoring.log_loss.toFixed(3)
            }
          />
        </div>
        <p className="mt-3 text-xs leading-5 text-zinc-500">
          Sample: {formatNumber(data.scoring.sample_size)} completed fixtures.
          Lower Brier score and log loss are better. This sample is descriptive,
          not a historical holdout.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-6 grid gap-4 lg:grid-cols-2">
      <LimitList
        title={`${productionModel.name} limits`}
        items={productionModel.limitations}
      />
      <LimitList
        title="Tournament and data limits"
        items={data.metadata.model_limitations}
      />
    </div>
  );
}

function StatusCell({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <div className="border-b border-white/10 p-5 sm:border-b-0 sm:border-l first:sm:border-l-0">
      <p className="font-mono text-[0.68rem] uppercase tracking-[0.14em] text-zinc-500">
        {label}
      </p>
      <p className="mt-2 text-xl font-semibold text-white">{value}</p>
      <p className="mt-1 text-xs text-zinc-500">{detail}</p>
    </div>
  );
}

function Evidence({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-black/20 p-4">
      <p className="font-mono text-[0.68rem] uppercase tracking-[0.12em] text-zinc-500">
        {label}
      </p>
      <p className="mt-2 text-lg font-semibold text-white">{value}</p>
    </div>
  );
}

function LimitList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-lg border border-[var(--score-amber)]/20 bg-[var(--score-amber)]/[0.05] p-4">
      <h3 className="text-sm font-semibold text-[var(--score-amber)]">
        {title}
      </h3>
      <ul className="mt-3 space-y-2 text-sm leading-6 text-zinc-300">
        {items.map((item) => (
          <li key={item} className="flex gap-2">
            <span aria-hidden="true">—</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

type MethodologySource = {
  name: string;
  url: string;
  usage: string;
};

function normalizeSource(
  source: Record<string, unknown>,
): MethodologySource | null {
  if (
    typeof source.name !== "string" ||
    typeof source.url !== "string" ||
    typeof source.usage !== "string"
  ) {
    return null;
  }
  return {
    name: source.name,
    url: source.url,
    usage: source.usage,
  };
}

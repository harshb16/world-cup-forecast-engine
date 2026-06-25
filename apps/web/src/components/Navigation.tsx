"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BarChart3,
  BookOpenText,
  Calendar,
  ChevronLeft,
  ChevronRight,
  FlaskConical,
  Gauge,
  GitBranch,
  Shield,
  Table2,
  TrendingUp,
  Trophy,
  Users,
} from "lucide-react";

import { DEFAULT_MODEL_TYPE, fetchMetadata } from "@/lib/api";
import { formatModelLabel } from "@/lib/format";
import { DataFreshness } from "@/components/DataFreshness";

const navItems = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/matchday", label: "Matchday", icon: Calendar },
  { href: "/bracket", label: "Bracket", icon: GitBranch },
  { href: "/groups", label: "Groups", icon: Table2 },
  { href: "/timeline", label: "Timeline", icon: TrendingUp },
  { href: "/what-if", label: "What-if", icon: FlaskConical },
  { href: "/teams", label: "Teams", icon: Users },
  { href: "/methodology", label: "Methodology", icon: BookOpenText },
  { href: "/models", label: "Models", icon: BarChart3 },
];

const COLLAPSE_STORAGE_KEY = "wco-nav-collapsed";

export function Navigation() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }
    return window.localStorage.getItem(COLLAPSE_STORAGE_KEY) === "true";
  });
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    fetchMetadata()
      .then((metadata) => {
        if (isActive) {
          setLastUpdated(metadata.last_updated);
        }
      })
      .catch(() => {
        if (isActive) {
          setLastUpdated(null);
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  function toggleCollapsed() {
    setCollapsed((current) => {
      const next = !current;
      window.localStorage.setItem(COLLAPSE_STORAGE_KEY, String(next));
      return next;
    });
  }

  return (
    <aside
      className={`flex w-full flex-col border-b border-white/10 bg-[#05070a]/95 px-4 py-4 transition-[width] lg:min-h-screen lg:border-b-0 ${
        collapsed ? "lg:w-16 lg:px-2" : "lg:w-72 lg:px-5"
      }`}
    >
      <Link
        href="/"
        className={`flex items-center px-2 ${collapsed ? "justify-center" : "gap-3"}`}
        title="World Cup Oracle"
      >
        <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-[var(--turf)] text-zinc-950">
          <Trophy size={22} aria-hidden="true" />
        </span>
        {!collapsed ? (
          <span>
            <span className="block text-base font-semibold text-[#f4f7f5]">
              World Cup Oracle
            </span>
            <span className="block font-mono text-xs font-medium uppercase tracking-[0.12em] text-[#93a19a]">
              Probability desk
            </span>
          </span>
        ) : null}
      </Link>

      <nav
        className={`mt-5 flex gap-1 overflow-x-auto lg:flex-col lg:overflow-visible ${
          collapsed ? "lg:items-center" : ""
        }`}
      >
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              title={item.label}
              className={`flex min-w-fit items-center rounded-md text-sm font-medium transition ${
                collapsed
                  ? "justify-center px-2 py-2 lg:w-10"
                  : "gap-2 px-3 py-2"
              } ${
                active
                  ? "bg-[var(--turf)] text-zinc-950"
                  : "text-[#93a19a] hover:bg-white/[0.06] hover:text-[#f4f7f5]"
              }`}
            >
              <Icon size={17} aria-hidden="true" />
              {!collapsed ? item.label : null}
            </Link>
          );
        })}
      </nav>

      <div className={`mt-4 ${collapsed ? "lg:px-0" : ""}`}>
        {!collapsed && lastUpdated ? (
          <p className="px-1 text-[0.68rem] leading-5 text-zinc-500">
            Data <DataFreshness timestamp={lastUpdated} compact />
          </p>
        ) : null}
      </div>

      {!collapsed ? (
        <div className="mt-auto hidden rounded-lg border border-white/10 bg-[#101722] p-3 text-sm text-[#f4f7f5] lg:block">
          <div className="flex items-center gap-2 font-semibold">
            <Shield size={16} aria-hidden="true" className="text-[var(--turf)]" />
            {formatModelLabel(DEFAULT_MODEL_TYPE)}
          </div>
          <p className="mt-1 text-xs leading-5 text-[#93a19a]">
            Current baseline using open international match results.
          </p>
        </div>
      ) : null}

      <button
        type="button"
        onClick={toggleCollapsed}
        className="mt-4 hidden items-center justify-center rounded-md border border-white/10 bg-white/[0.04] p-2 text-zinc-400 transition hover:bg-white/[0.08] hover:text-zinc-100 lg:flex"
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  );
}

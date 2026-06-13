"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  FlaskConical,
  Gauge,
  GitBranch,
  History,
  Shield,
  Table2,
  Trophy,
  Users,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/bracket", label: "Bracket", icon: GitBranch },
  { href: "/groups", label: "Groups", icon: Table2 },
  { href: "/what-if", label: "What-if", icon: FlaskConical },
  { href: "/teams", label: "Teams", icon: Users },
  { href: "/models", label: "Models", icon: BarChart3 },
  { href: "/backtesting", label: "Backtesting", icon: History },
];

export function Navigation() {
  const pathname = usePathname();

  return (
    <aside className="flex w-full flex-col border-b border-white/10 bg-[#090d18]/95 px-4 py-4 backdrop-blur lg:min-h-screen lg:w-72 lg:border-b-0 lg:border-r lg:px-5">
      <Link href="/" className="flex items-center gap-3 px-2">
        <span className="flex size-10 items-center justify-center rounded-lg bg-emerald-300 text-zinc-950">
          <Trophy size={22} aria-hidden="true" />
        </span>
        <span>
          <span className="block text-base font-semibold text-white">
            World Cup Oracle
          </span>
          <span className="block text-xs font-medium text-zinc-400">
            Match probability desk
          </span>
        </span>
      </Link>

      <nav className="mt-5 flex gap-1 overflow-x-auto lg:flex-col lg:overflow-visible">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex min-w-fit items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition ${
                pathname === item.href
                  ? "bg-white/10 text-white"
                  : "text-zinc-400 hover:bg-white/[0.06] hover:text-zinc-100"
              }`}
            >
              <Icon size={17} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto hidden rounded-lg border border-white/10 bg-white/[0.05] p-3 text-sm text-zinc-100 lg:block">
        <div className="flex items-center gap-2 font-semibold">
          <Shield size={16} aria-hidden="true" className="text-emerald-200" />
          MVP model
        </div>
        <p className="mt-1 text-xs leading-5 text-zinc-400">
          Real data, 2026 bracket slots, seeded reveal lab.
        </p>
      </div>
    </aside>
  );
}

import Link from "next/link";
import {
  BarChart3,
  FlaskConical,
  Gauge,
  History,
  Shield,
  Table2,
  Trophy,
  Users,
} from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/groups", label: "Groups", icon: Table2 },
  { href: "/what-if", label: "What-if", icon: FlaskConical },
  { href: "/teams", label: "Teams", icon: Users },
  { href: "/models", label: "Models", icon: BarChart3 },
  { href: "/backtesting", label: "Backtesting", icon: History },
];

export function Navigation() {
  return (
    <aside className="flex w-full flex-col border-b border-zinc-200 bg-white/90 px-4 py-4 backdrop-blur lg:min-h-screen lg:w-72 lg:border-b-0 lg:border-r lg:px-5">
      <Link href="/" className="flex items-center gap-3 px-2">
        <span className="flex size-10 items-center justify-center rounded-lg bg-emerald-600 text-white">
          <Trophy size={22} aria-hidden="true" />
        </span>
        <span>
          <span className="block text-base font-semibold text-zinc-950">
            World Cup Oracle
          </span>
          <span className="block text-xs font-medium text-zinc-500">
            Simulation console
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
              className="flex min-w-fit items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-950"
            >
              <Icon size={17} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto hidden rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950 lg:block">
        <div className="flex items-center gap-2 font-semibold">
          <Shield size={16} aria-hidden="true" />
          MVP model
        </div>
        <p className="mt-1 text-xs leading-5 text-amber-800">
          Sample data and placeholder bracket are active.
        </p>
      </div>
    </aside>
  );
}

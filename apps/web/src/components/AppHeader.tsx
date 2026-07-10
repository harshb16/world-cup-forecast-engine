"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BarChart3,
  BookOpenText,
  Calendar,
  Database,
  FlaskConical,
  Gauge,
  GitBranch,
  History,
  Menu,
  MoreHorizontal,
  Shield,
  Table2,
  TrendingUp,
  Trophy,
  Users,
  type LucideIcon,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { DataFreshness } from "@/components/DataFreshness";
import { FrozenDatasetBadge } from "@/components/FrozenDatasetBadge";
import { DEFAULT_MODEL_TYPE, fetchMetadata } from "@/lib/api";
import { formatModelLabel } from "@/lib/format";
import { cn } from "@/lib/utils";
import { useTimeMachine } from "@/components/time-machine/TimeMachineProvider";

type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

const liveNav: NavItem[] = [
  { href: "/", label: "Dashboard", icon: Gauge },
  { href: "/matchday", label: "Matchday", icon: Calendar },
  { href: "/bracket", label: "Bracket", icon: GitBranch },
];

const exploreNav: NavItem[] = [
  { href: "/groups", label: "Groups", icon: Table2 },
  { href: "/teams", label: "Teams", icon: Users },
  { href: "/time-machine", label: "Replay", icon: TrendingUp },
  { href: "/data-status", label: "Data Status", icon: Database },
];

const labNav: NavItem[] = [
  { href: "/what-if", label: "What-if", icon: FlaskConical },
  { href: "/models", label: "Models", icon: BarChart3 },
];

const systemNav: NavItem[] = [
  { href: "/retrospective", label: "Retrospective", icon: History },
  { href: "/methodology", label: "Methodology", icon: BookOpenText },
];

const allNavItems = [...liveNav, ...exploreNav, ...labNav, ...systemNav];

function NavLink({
  item,
  active,
  onNavigate,
  compact = false,
}: {
  item: NavItem;
  active: boolean;
  onNavigate?: () => void;
  compact?: boolean;
}) {
  const Icon = item.icon;
  const { hrefFor } = useTimeMachine();
  return (
    <Link
      href={hrefFor(item.href)}
      onClick={onNavigate}
      className={cn(
        "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition",
        compact ? "w-full" : "whitespace-nowrap",
        active
          ? "bg-primary text-primary-foreground shadow-[0_0_20px_color-mix(in_oklch,var(--primary)_35%,transparent)]"
          : "text-muted-foreground hover:bg-accent/80 hover:text-foreground",
      )}
    >
      <Icon aria-hidden="true" />
      {item.label}
    </Link>
  );
}

function NavGroup({
  label,
  items,
  pathname,
  onNavigate,
}: {
  label: string;
  items: NavItem[];
  pathname: string;
  onNavigate?: () => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <p className="px-3 text-eyebrow">{label}</p>
      {items.map((item) => (
        <NavLink
          key={item.href}
          item={item}
          active={pathname === item.href}
          onNavigate={onNavigate}
          compact
        />
      ))}
    </div>
  );
}

export function AppHeader() {
  const pathname = usePathname();
  const { hrefFor, isReplay } = useTimeMachine();
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [frozenLabel, setFrozenLabel] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const activePage =
    allNavItems.find((item) => item.href === pathname)?.label ?? "World Cup Oracle";

  useEffect(() => {
    let isActive = true;
    fetchMetadata()
      .then((metadata) => {
        if (isActive) {
          setLastUpdated(metadata.last_updated);
          setFrozenLabel(metadata.is_frozen ? metadata.frozen_label : null);
        }
      })
      .catch(() => {
        if (isActive) {
          setLastUpdated(null);
          setFrozenLabel(null);
        }
      });
    return () => {
      isActive = false;
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-background/80 shadow-[0_8px_32px_color-mix(in_oklch,var(--background)_55%,transparent)] backdrop-blur-md supports-[backdrop-filter]:bg-background/70">
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-primary/45 to-transparent" />
      <div className="mx-auto flex h-14 max-w-[100vw] items-center gap-3 px-4 sm:px-6 lg:px-8">
        <Link href={hrefFor("/")} className="flex shrink-0 items-center gap-2.5">
          <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Trophy aria-hidden="true" />
          </span>
          <span className="hidden sm:block">
            <span className="block text-sm font-semibold leading-tight text-foreground">
              World Cup Oracle
            </span>
            <span className="block font-mono text-[0.65rem] uppercase tracking-widest text-muted-foreground">
              Probability desk
            </span>
          </span>
        </Link>

        <nav
          className="hidden items-center gap-0.5 xl:flex"
          aria-label="Primary"
        >
          {liveNav.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              active={pathname === item.href}
            />
          ))}
          <span className="mx-1 h-4 w-px bg-border" aria-hidden="true" />
          {exploreNav.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              active={pathname === item.href}
            />
          ))}
          <span className="mx-1 hidden h-4 w-px bg-border xl:block" aria-hidden="true" />
          <div className="hidden xl:contents">
            {labNav.map((item) => (
              <NavLink
                key={item.href}
                item={item}
                active={pathname === item.href}
              />
            ))}
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button variant="ghost" size="sm" className="gap-1.5">
                  <MoreHorizontal aria-hidden="true" />
                  More
                </Button>
              }
            />
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel className="xl:hidden">Lab</DropdownMenuLabel>
              {labNav.map((item) => (
                <DropdownMenuItem
                  key={item.href}
                  render={<Link href={hrefFor(item.href)} />}
                >
                  <item.icon aria-hidden="true" />
                  {item.label}
                </DropdownMenuItem>
              ))}
              <DropdownMenuSeparator />
              <DropdownMenuLabel>System</DropdownMenuLabel>
              {systemNav.map((item) => (
                <DropdownMenuItem
                  key={item.href}
                  render={<Link href={hrefFor(item.href)} />}
                >
                  <item.icon aria-hidden="true" />
                  {item.label}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </nav>

        <p className="truncate text-sm font-medium text-muted-foreground xl:hidden">
          {activePage}
        </p>

        <div className="ml-auto flex items-center gap-2">
          {isReplay ? (
            <p className="hidden text-[0.68rem] font-semibold text-primary md:block">
              Reconstructed replay
            </p>
          ) : frozenLabel ? (
            <p className="hidden text-[0.68rem] text-muted-foreground md:block">
              <FrozenDatasetBadge label={frozenLabel} compact />
            </p>
          ) : lastUpdated ? (
            <p className="hidden text-[0.68rem] text-muted-foreground md:block">
              Data <DataFreshness timestamp={lastUpdated} compact />
            </p>
          ) : null}
          <Link href={hrefFor("/models")} className="hidden 2xl:block">
            <Badge variant="secondary" className="gap-1.5 font-normal">
              <Shield aria-hidden="true" />
              {formatModelLabel(DEFAULT_MODEL_TYPE)}
            </Badge>
          </Link>

          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger
              render={
                <Button
                  variant="outline"
                  size="icon"
                  className="xl:hidden"
                  aria-label="Open navigation menu"
                />
              }
            >
              <Menu aria-hidden="true" />
            </SheetTrigger>
            <SheetContent side="left" className="w-[min(100vw-2rem,20rem)]">
              <SheetHeader>
                <SheetTitle>Navigate</SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-6 overflow-y-auto px-1 pb-6">
                <NavGroup
                  label="Live"
                  items={liveNav}
                  pathname={pathname}
                  onNavigate={() => setMobileOpen(false)}
                />
                <NavGroup
                  label="Explore"
                  items={exploreNav}
                  pathname={pathname}
                  onNavigate={() => setMobileOpen(false)}
                />
                <NavGroup
                  label="Lab"
                  items={labNav}
                  pathname={pathname}
                  onNavigate={() => setMobileOpen(false)}
                />
                <NavGroup
                  label="System"
                  items={systemNav}
                  pathname={pathname}
                  onNavigate={() => setMobileOpen(false)}
                />
                <Link
                  href={hrefFor("/models")}
                  onClick={() => setMobileOpen(false)}
                  className="mx-3 rounded-lg border border-border bg-card p-3 text-sm"
                >
                  <div className="flex items-center gap-2 font-semibold text-foreground">
                    <Shield className="text-primary" aria-hidden="true" />
                    {formatModelLabel(DEFAULT_MODEL_TYPE)}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Current baseline model
                  </p>
                </Link>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}

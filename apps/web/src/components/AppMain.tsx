"use client";

import { usePathname } from "next/navigation";

import { PageShell } from "@/components/ui/PageShell";

export function AppMain({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const fullBleed = pathname === "/bracket";

  return <PageShell width={fullBleed ? "full" : "default"}>{children}</PageShell>;
}

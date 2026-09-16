"use client";

import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";

export function TeamSearch({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="relative">
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted-foreground"
      />
      <Input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search teams"
        className="h-11 pl-10"
      />
    </div>
  );
}

"use client";

import { Search } from "lucide-react";

export function TeamSearch({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="relative block">
      <Search
        size={17}
        aria-hidden="true"
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400"
      />
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search teams"
        className="h-11 w-full rounded-md border border-white/10 bg-[#101624] pl-10 pr-3 text-sm text-white outline-none transition placeholder:text-zinc-500 focus:border-emerald-300/50"
      />
    </label>
  );
}

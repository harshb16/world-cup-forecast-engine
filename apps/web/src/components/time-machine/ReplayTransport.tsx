"use client";

import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useTimeMachine } from "./TimeMachineProvider";

export function ReplayTransport() {
  const { isReplay, manifest, milestoneId, selectMilestone, statusMessage } = useTimeMachine();
  const [playing, setPlaying] = useState(false);
  const available = useMemo(
    () => manifest?.milestones.filter((item) => item.available) ?? [],
    [manifest],
  );
  const index = available.findIndex((item) => item.id === milestoneId);

  useEffect(() => {
    if (!playing || index < 0 || index >= available.length - 1) return;
    const timer = window.setTimeout(() => {
      selectMilestone(available[index + 1].id);
      if (index + 1 === available.length - 1) setPlaying(false);
    }, 2_500);
    return () => window.clearTimeout(timer);
  }, [available, index, playing, selectMilestone]);

  if (!isReplay || !manifest || index < 0) return null;
  const selected = available[index];
  const select = (id: string) => {
    setPlaying(false);
    selectMilestone(id);
  };

  return (
    <section className="border-b border-primary/20 bg-primary/[0.06]" aria-label="Replay controls">
      <p className="sr-only" role="status" aria-live="polite">{statusMessage}</p>
      <div className="mx-auto flex max-w-[1600px] items-center gap-3 px-4 py-2 sm:px-6 lg:px-8">
        <Button size="icon-sm" variant="ghost" disabled={index === 0} onClick={() => select(available[index - 1].id)} aria-label="Previous milestone">
          <ChevronLeft />
        </Button>
        <Button size="icon-sm" variant="ghost" disabled={index === available.length - 1} onClick={() => setPlaying((value) => !value)} aria-label={playing ? "Pause replay" : "Play replay"}>
          {playing ? <Pause /> : <Play />}
        </Button>
        <div className="hidden min-w-0 flex-1 items-center gap-2 md:flex">
          <span className="text-xs text-muted-foreground">Kickoff</span>
          {available.map((item) => (
            <button key={item.id} type="button" onClick={() => select(item.id)} aria-label={item.label} aria-current={item.id === selected.id ? "step" : undefined} className={`h-3 flex-1 rounded-full transition motion-reduce:transition-none ${item.order <= selected.order ? "bg-primary" : "bg-border"}`} />
          ))}
          <span className="text-xs text-muted-foreground">Final</span>
        </div>
        <select className="min-w-0 flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm md:hidden" value={selected.id} onChange={(event) => select(event.target.value)} aria-label="Selected replay milestone">
          {available.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
        </select>
        <p className="hidden min-w-52 text-right text-xs font-semibold sm:block">Selected: {selected.label}</p>
        <Button size="icon-sm" variant="ghost" disabled={index === available.length - 1} onClick={() => select(available[index + 1].id)} aria-label="Next milestone">
          <ChevronRight />
        </Button>
      </div>
    </section>
  );
}

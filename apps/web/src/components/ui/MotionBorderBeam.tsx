"use client";

import { useEffect, useState } from "react";

import { BorderBeam } from "@/components/ui/border-beam";

export function MotionBorderBeam(
  props: React.ComponentProps<typeof BorderBeam>,
) {
  const [reduceMotion, setReduceMotion] = useState(true);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduceMotion(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  if (reduceMotion) {
    return null;
  }

  return <BorderBeam {...props} />;
}

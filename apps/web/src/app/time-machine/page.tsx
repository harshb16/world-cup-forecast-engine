import { redirect } from "next/navigation";

import { ReplayLanding } from "@/components/time-machine/ReplayLanding";

export default async function TimeMachinePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const query = await searchParams;
  if (!query.at) {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      for (const item of Array.isArray(value) ? value : [value]) {
        if (item !== undefined) params.append(key, item);
      }
    }
    params.set("at", "before_group_md1");
    redirect(`/time-machine?${params}`);
  }
  return <ReplayLanding />;
}

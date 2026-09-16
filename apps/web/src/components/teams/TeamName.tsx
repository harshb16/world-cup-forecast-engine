import Link from "next/link";

import { Team } from "@/lib/api";

export function TeamName({
  team,
  groupName,
  href,
}: {
  team: Team;
  groupName?: string;
  href?: string;
}) {
  const content = (
    <>
      <span className="block font-semibold text-foreground">{team.name}</span>
      <span className="block text-xs text-muted-foreground">
        {groupName ?? team.group_id} · Rating {team.rating.toFixed(0)}
      </span>
    </>
  );

  if (href) {
    return (
      <Link href={href} className="block transition hover:opacity-80">
        {content}
      </Link>
    );
  }

  return <div>{content}</div>;
}

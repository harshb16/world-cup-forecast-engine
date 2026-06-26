import { ProbabilityBar } from "@/components/dashboard/ProbabilityBar";
import { SectionCard } from "@/components/ui/SectionCard";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatPercent } from "@/lib/format";
import { TeamProbability } from "@/lib/api";

export function ChampionOddsTable({ teams }: { teams: TeamProbability[] }) {
  const rows = [...teams].sort((a, b) => b.champion - a.champion).slice(0, 12);

  return (
    <SectionCard
      title="Champion odds"
      description="Chance each contender wins the tournament across the simulation run."
    >
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Team</TableHead>
              <TableHead>Group</TableHead>
              <TableHead>Champion</TableHead>
              <TableHead className="text-right">Average points</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((team, index) => (
              <TableRow
                key={team.team_id}
                className={index % 2 === 1 ? "bg-muted/25" : undefined}
              >
                <TableCell className="font-medium">{team.team_name}</TableCell>
                <TableCell className="text-muted-foreground">
                  {team.group_id}
                </TableCell>
                <TableCell className="min-w-[10rem]">
                  <ProbabilityBar value={team.champion} showLabel={false} />
                  <span className="mt-1 block font-mono text-xs tabular-nums text-muted-foreground">
                    {formatPercent(team.champion)}
                  </span>
                </TableCell>
                <TableCell className="text-right font-mono tabular-nums text-muted-foreground">
                  {team.average_points.toFixed(2)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <p className="mt-3 text-xs text-muted-foreground">
        Top 12 teams shown. Total champion probability:{" "}
        {formatPercent(teams.reduce((total, team) => total + team.champion, 0))}
      </p>
    </SectionCard>
  );
}

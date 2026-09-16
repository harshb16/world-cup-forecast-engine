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
import { TeamProbability } from "@/lib/api";

export function StageProbabilityTable({ teams }: { teams: TeamProbability[] }) {
  const rows = [...teams]
    .sort(
      (a, b) =>
        b.group_qualification_probability - a.group_qualification_probability,
    )
    .slice(0, 12);

  return (
    <SectionCard
      title="Stage probabilities"
      description="How often top teams reach each checkpoint in the bracket."
    >
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Team</TableHead>
              <TableHead>Qualify</TableHead>
              <TableHead>Semi-final</TableHead>
              <TableHead>Final</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((team, index) => (
              <TableRow
                key={team.team_id}
                className={index % 2 === 1 ? "bg-muted/25" : undefined}
              >
                <TableCell className="font-medium">{team.team_name}</TableCell>
                <TableCell className="min-w-[8rem]">
                  <ProbabilityBar
                    value={team.group_qualification_probability}
                    showLabel={false}
                  />
                </TableCell>
                <TableCell className="min-w-[8rem]">
                  <ProbabilityBar value={team.semi_final} tone="amber" showLabel={false} />
                </TableCell>
                <TableCell className="min-w-[8rem]">
                  <ProbabilityBar value={team.final} tone="rose" showLabel={false} />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </SectionCard>
  );
}

import { DeltaBadge } from "@/components/ui/DeltaBadge";
import { SectionCard } from "@/components/ui/SectionCard";
import { TeamProbabilityDelta } from "@/lib/api";

export function ScenarioResultDeltaTable({
  title,
  rows,
}: {
  title: string;
  rows: TeamProbabilityDelta[];
}) {
  return (
    <SectionCard>
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-muted-foreground">
            <tr>
              <th className="py-2 font-semibold">Team</th>
              <th className="py-2 font-semibold">Champion</th>
              <th className="py-2 font-semibold">Final</th>
              <th className="py-2 font-semibold">Semi</th>
              <th className="py-2 font-semibold">Quarter</th>
              <th className="py-2 font-semibold">Round of 16</th>
              <th className="py-2 font-semibold">Qualify</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {rows.map((row) => (
              <tr key={row.team_id}>
                <td className="py-3 font-medium text-foreground">
                  {row.team_name}
                </td>
                <td className="py-3">
                  <DeltaBadge value={row.champion_probability_delta} />
                </td>
                <td className="py-3">
                  <DeltaBadge value={row.final_probability_delta} />
                </td>
                <td className="py-3">
                  <DeltaBadge value={row.semi_final_probability_delta} />
                </td>
                <td className="py-3">
                  <DeltaBadge value={row.quarter_final_probability_delta} />
                </td>
                <td className="py-3">
                  <DeltaBadge value={row.round_of_16_probability_delta} />
                </td>
                <td className="py-3">
                  <DeltaBadge value={row.group_qualification_probability_delta} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

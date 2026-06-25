"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { CalibrationBin } from "@/lib/api";
import { formatPercent } from "@/lib/format";

type CalibrationChartProps = {
  bins: CalibrationBin[];
};

export function CalibrationChart({ bins }: CalibrationChartProps) {
  const data = bins
    .filter((bin) => bin.count > 0)
    .map((bin) => ({
      midpoint: bin.predicted_midpoint,
      actual: bin.actual_frequency,
      perfect: bin.predicted_midpoint,
      count: bin.count,
    }));

  if (data.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Not enough completed fixtures to plot calibration yet.
      </p>
    );
  }

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
          <XAxis
            dataKey="midpoint"
            tickFormatter={(value: number) => formatPercent(value)}
            stroke="#71717a"
            fontSize={12}
          />
          <YAxis
            tickFormatter={(value: number) => formatPercent(value)}
            stroke="#71717a"
            fontSize={12}
            domain={[0, 1]}
          />
          <Tooltip
            contentStyle={{
              background: "#0f1720",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "0.5rem",
            }}
            formatter={(value, name, item) => {
              const numeric = typeof value === "number" ? value : 0;
              if (name === "actual") {
                const count =
                  item && typeof item === "object" && "payload" in item
                    ? (item.payload as { count?: number }).count ?? 0
                    : 0;
                return [formatPercent(numeric), `Actual (${count} samples)`];
              }
              return [formatPercent(numeric), "Perfect calibration"];
            }}
            labelFormatter={(label) => `Predicted ${formatPercent(Number(label))}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="perfect"
            name="Perfect calibration"
            stroke="#71717a"
            strokeDasharray="4 4"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Model"
            stroke="#34d399"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

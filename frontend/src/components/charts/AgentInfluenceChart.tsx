"use client";

import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";

interface AgentInfluenceChartProps {
  data: Array<{ axis: string; value: number }>;
  color?: string;
}

export function AgentInfluenceChart({ data, color = "#4f46e5" }: AgentInfluenceChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-hud-muted font-mono text-sm">
        No data yet
      </div>
    );
  }

  return (
    <div className="w-full h-48">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="#2a2a3a" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: "#6a6a80", fontSize: 9, fontFamily: "JetBrains Mono" }}
          />
          <Radar
            name="Influence"
            dataKey="value"
            stroke={color}
            fill={color + "30"}
            fillOpacity={0.6}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

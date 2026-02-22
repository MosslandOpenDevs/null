"use client";

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import type { FactionData } from "@/stores/simulation";

interface FactionPowerChartProps {
  data: Array<{ epoch: number; [factionName: string]: number }>;
  factions: FactionData[];
}

export function FactionPowerChart({ data, factions }: FactionPowerChartProps) {
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
        <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <XAxis
            dataKey="epoch"
            tick={{ fill: "#6a6a80", fontSize: 10, fontFamily: "JetBrains Mono" }}
            axisLine={{ stroke: "#2a2a3a" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#6a6a80", fontSize: 10, fontFamily: "JetBrains Mono" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#111118",
              border: "1px solid #2a2a3a",
              fontFamily: "JetBrains Mono",
              fontSize: 11,
              color: "#e0dfd8",
            }}
          />
          {factions.map((f) => (
            <Area
              key={f.id}
              type="monotone"
              dataKey={f.name}
              stackId="1"
              fill={f.color + "40"}
              stroke={f.color}
              strokeWidth={1.5}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

"use client";

import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const THEME_COLORS: Record<string, string> = {
  conflict: "#ff4466",
  cooperation: "#4488ff",
  discovery: "#ffaa33",
  governance: "#a855f7",
  culture: "#33ff88",
};

interface ThemeEvolutionChartProps {
  data: Array<{ epoch: number; [theme: string]: number }>;
  themes: string[];
}

export function ThemeEvolutionChart({ data, themes }: ThemeEvolutionChartProps) {
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
          {themes.map((theme) => (
            <Area
              key={theme}
              type="monotone"
              dataKey={theme}
              stackId="1"
              fill={(THEME_COLORS[theme] || "#6366f1") + "40"}
              stroke={THEME_COLORS[theme] || "#6366f1"}
              strokeWidth={1.5}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

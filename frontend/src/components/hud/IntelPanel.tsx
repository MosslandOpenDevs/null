"use client";

import { useSimulationStore } from "@/stores/simulation";
import { CornerMark } from "./CornerMark";
import { AgentTab } from "./IntelTabs/AgentTab";
import { WikiTab } from "./IntelTabs/WikiTab";
import { GraphTab } from "./IntelTabs/GraphTab";
import { LogTab } from "./IntelTabs/LogTab";
import { ResonanceTab } from "./IntelTabs/ResonanceTab";
import { StrataTab } from "./IntelTabs/StrataTab";

const TABS = [
  { id: "agent" as const, label: "AGENT" },
  { id: "wiki" as const, label: "WIKI" },
  { id: "graph" as const, label: "GRAPH" },
  { id: "log" as const, label: "LOG" },
  { id: "resonance" as const, label: "RESONANCE" },
  { id: "strata" as const, label: "STRATA" },
];

export function IntelPanel() {
  const { intelTab, setIntelTab } = useSimulationStore();

  return (
    <div className="relative flex flex-col h-full bg-void-light border-l border-hud-border w-[350px] min-w-[350px]">
      <CornerMark />
      {/* Tab bar */}
      <div className="flex border-b border-hud-border">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setIntelTab(tab.id)}
            className={`flex-1 py-2 font-mono text-[10px] uppercase tracking-[0.15em] transition-colors border-b-2 ${
              intelTab === tab.id
                ? "text-accent border-accent"
                : "text-hud-muted border-transparent hover:text-hud-text"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {intelTab === "agent" && <AgentTab />}
        {intelTab === "wiki" && <WikiTab />}
        {intelTab === "graph" && <GraphTab />}
        {intelTab === "log" && <LogTab />}
        {intelTab === "resonance" && <ResonanceTab />}
        {intelTab === "strata" && <StrataTab />}
      </div>
    </div>
  );
}

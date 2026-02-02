"use client";

import { useSimulationStore } from "@/stores/simulation";
import { AgentTab } from "./hud/IntelTabs/AgentTab";
import { WikiTab } from "./hud/IntelTabs/WikiTab";
import { GraphTab } from "./hud/IntelTabs/GraphTab";
import { LogTab } from "./hud/IntelTabs/LogTab";
import { StrataTab } from "./hud/IntelTabs/StrataTab";
import { ResonanceTab } from "./hud/IntelTabs/ResonanceTab";
import { ExportTab } from "./ExportTab";

const TABS = [
  { id: "wiki" as const, label: "WIKI" },
  { id: "graph" as const, label: "GRAPH" },
  { id: "strata" as const, label: "STRATA" },
  { id: "resonance" as const, label: "RESONANCE" },
  { id: "agent" as const, label: "AGENT" },
  { id: "log" as const, label: "LOG" },
  { id: "export" as const, label: "EXPORT" },
];

export function KnowledgeHub() {
  const { intelTab, setIntelTab } = useSimulationStore();

  // Default to wiki if current tab isn't in our list
  const activeTab = TABS.some((t) => t.id === intelTab) ? intelTab : "wiki";

  return (
    <div className="flex flex-col h-full min-w-0">
      {/* Tab bar */}
      <div className="flex border-b border-hud-border bg-void-light">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setIntelTab(tab.id)}
            className={`px-4 py-2.5 font-mono text-[10px] uppercase tracking-[0.15em] transition-colors border-b-2 ${
              activeTab === tab.id
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
        {activeTab === "wiki" && <WikiTab />}
        {activeTab === "graph" && <GraphTab />}
        {activeTab === "strata" && <StrataTab />}
        {activeTab === "resonance" && <ResonanceTab />}
        {activeTab === "agent" && <AgentTab />}
        {activeTab === "log" && <LogTab />}
        {activeTab === "export" && <ExportTab />}
      </div>
    </div>
  );
}

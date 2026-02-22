"use client";

import { useMemo } from "react";
import { useSimulationStore } from "@/stores/simulation";

interface ActiveAgentsProps {
  activeAgentIds: Set<string>;
  onAgentClick?: (agentId: string) => void;
}

export function ActiveAgents({ activeAgentIds, onAgentClick }: ActiveAgentsProps) {
  const { agents, factions } = useSimulationStore();

  const factionMap = useMemo(
    () => new Map(factions.map((f) => [f.id, f])),
    [factions]
  );

  const sortedAgents = useMemo(() => {
    return [...agents].sort((a, b) => {
      const aActive = activeAgentIds.has(a.id) ? 0 : 1;
      const bActive = activeAgentIds.has(b.id) ? 0 : 1;
      return aActive - bActive || a.name.localeCompare(b.name);
    });
  }, [agents, activeAgentIds]);

  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-hud-label mb-1.5">
        AGENTS ({activeAgentIds.size} active)
      </div>
      <div className="space-y-0.5 max-h-48 overflow-y-auto">
        {sortedAgents.map((agent) => {
          const isActive = activeAgentIds.has(agent.id);
          const faction = agent.faction_id ? factionMap.get(agent.faction_id) : null;
          const color = faction?.color || "#6366f1";

          return (
            <button
              key={agent.id}
              onClick={() => onAgentClick?.(agent.id)}
              className={`flex items-center gap-1.5 w-full text-left py-0.5 px-1 rounded-sm hover:bg-void-alt transition-colors ${
                isActive ? "" : "opacity-30"
              }`}
            >
              <span
                className={isActive ? "animate-pulse" : ""}
                style={{ color }}
              >
                ●
              </span>
              <span className="font-mono text-[11px] text-hud-text truncate">
                {agent.name}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

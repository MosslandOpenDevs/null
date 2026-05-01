"use client";

import { RelationGraph } from "./RelationGraph";
import { FactionPowerBar } from "./FactionPowerBar";
import { ActiveAgents } from "./ActiveAgents";

interface MinimapSidebarProps {
  className?: string;
  activeAgentIds: Set<string>;
  onAgentClick?: (agentId: string) => void;
  onFactionClick?: (factionId: string) => void;
}

export function MinimapSidebar({
  className,
  activeAgentIds,
  onAgentClick,
  onFactionClick,
}: MinimapSidebarProps) {
  return (
    <div className={`flex flex-col border-l border-hud-border bg-void-light overflow-y-auto ${className || ""}`}>
      {/* Relation Network */}
      <div className="px-3 pt-3 pb-2 border-b border-hud-border">
        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-hud-label mb-1">
          RELATION NETWORK
        </div>
        <RelationGraph
          onAgentClick={onAgentClick}
          activeAgentIds={activeAgentIds}
        />
      </div>

      {/* Faction Power */}
      <div className="px-3 py-2 border-b border-hud-border">
        <FactionPowerBar onFactionClick={onFactionClick} />
      </div>

      {/* Active Agents */}
      <div className="px-3 py-2 flex-1">
        <ActiveAgents
          activeAgentIds={activeAgentIds}
          onAgentClick={onAgentClick}
        />
      </div>
    </div>
  );
}

"use client";

import { useSimulationStore } from "@/stores/simulation";

interface FactionPowerBarProps {
  onFactionClick?: (factionId: string) => void;
}

export function FactionPowerBar({ onFactionClick }: FactionPowerBarProps) {
  const { factions, agents, relationships } = useSimulationStore();

  // Calculate faction power: agent count × average relationship strength
  const factionPower = factions.map((f) => {
    const factionAgents = agents.filter((a) => a.faction_id === f.id);
    const agentIds = new Set(factionAgents.map((a) => a.id));

    let totalStrength = 0;
    let relCount = 0;
    for (const r of relationships) {
      if (agentIds.has(r.agent_a) || agentIds.has(r.agent_b)) {
        totalStrength += Math.max(0, r.strength);
        relCount++;
      }
    }

    const avgStrength = relCount > 0 ? totalStrength / relCount : 0.5;
    return {
      id: f.id,
      name: f.name,
      color: f.color,
      power: factionAgents.length * (0.5 + avgStrength),
      agentCount: factionAgents.length,
    };
  });

  const totalPower = factionPower.reduce((sum, f) => sum + f.power, 0) || 1;

  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-hud-label mb-1.5">
        FACTION POWER
      </div>
      <div className="flex h-3 rounded-sm overflow-hidden bg-void">
        {factionPower.map((f) => (
          <div
            key={f.id}
            className="cursor-pointer hover:brightness-125 transition-all duration-500"
            style={{
              width: `${(f.power / totalPower) * 100}%`,
              backgroundColor: f.color,
              minWidth: f.agentCount > 0 ? "8px" : "0",
            }}
            title={`${f.name}: ${f.agentCount} agents`}
            onClick={() => onFactionClick?.(f.id)}
          />
        ))}
      </div>
      <div className="flex gap-2 mt-1.5 flex-wrap">
        {factionPower.map((f) => (
          <button
            key={f.id}
            onClick={() => onFactionClick?.(f.id)}
            className="font-mono text-[9px] text-hud-muted hover:text-hud-text transition-colors"
          >
            <span style={{ color: f.color }}>●</span> {f.name}
          </button>
        ))}
      </div>
    </div>
  );
}

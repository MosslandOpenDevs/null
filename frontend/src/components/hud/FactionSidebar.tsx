"use client";

import { useSimulationStore } from "@/stores/simulation";
import { CornerMark } from "./CornerMark";

export function FactionSidebar() {
  const { factions, agents, relationships, selectedFaction, setSelectedFaction, setSelectedAgent, setIntelTab } =
    useSimulationStore();

  // Derive factions from world config if API factions are empty
  const world = useSimulationStore((s) => s.world);
  const displayFactions = factions.length > 0
    ? factions
    : ((world?.config as Record<string, unknown>)?.factions as Array<Record<string, unknown>> || []).map((f, i) => ({
        id: String(i),
        world_id: world?.id || "",
        name: String(f.name || ""),
        description: String(f.description || ""),
        color: String(f.color || "#6366f1"),
        agent_count: Number(f.agent_count || 0),
      }));

  const totalAgents = displayFactions.reduce((sum, f) => sum + f.agent_count, 0) || agents.length;

  // Get agents for a faction
  const getAgentsForFaction = (factionId: string) => {
    if (factions.length > 0) {
      return agents.filter((a) => a.faction_id === factionId).slice(0, 5);
    }
    // Fallback: distribute agents by index
    const idx = displayFactions.findIndex((f) => f.id === factionId);
    const perFaction = Math.ceil(agents.length / Math.max(displayFactions.length, 1));
    return agents.slice(idx * perFaction, (idx + 1) * perFaction).slice(0, 5);
  };

  // Build simple faction-to-faction relationship summary
  const getRelationType = (fIdA: string, fIdB: string): string | null => {
    const agentsA = new Set(agents.filter((a) => a.faction_id === fIdA).map((a) => a.id));
    const agentsB = new Set(agents.filter((a) => a.faction_id === fIdB).map((a) => a.id));

    const relevant = relationships.filter(
      (r) =>
        (agentsA.has(r.agent_a) && agentsB.has(r.agent_b)) ||
        (agentsA.has(r.agent_b) && agentsB.has(r.agent_a))
    );
    if (relevant.length === 0) return null;

    const typeCounts: Record<string, number> = {};
    for (const r of relevant) {
      typeCounts[r.type] = (typeCounts[r.type] || 0) + 1;
    }
    return Object.entries(typeCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || "neutral";
  };

  const typeColor: Record<string, string> = {
    ally: "#22c55e",
    rival: "#ef4444",
    neutral: "#5a5a6e",
    trade: "#22d3ee",
    mentor: "#6366f1",
  };

  return (
    <div className="flex flex-col h-full bg-void-light border-r border-hud-border w-[250px] min-w-[250px] overflow-y-auto">
      {/* Header */}
      <div className="px-3 py-2 border-b border-hud-border">
        <span className="font-mono text-[13px] uppercase tracking-[0.2em] text-hud-label">
          FACTION OVERVIEW
        </span>
      </div>

      {/* Faction list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {displayFactions.map((faction) => {
          const isSelected = selectedFaction === faction.id;
          const factionAgents = getAgentsForFaction(faction.id);
          const power = totalAgents > 0 ? (faction.agent_count / totalAgents) * 100 : 0;

          return (
            <div
              key={faction.id}
              className="relative p-2 border border-hud-border cursor-pointer transition-colors hover:border-hud-border-active"
              style={{
                borderColor: isSelected ? faction.color + "80" : undefined,
                backgroundColor: isSelected ? faction.color + "08" : undefined,
              }}
              onClick={() => setSelectedFaction(isSelected ? null : faction.id)}
            >
              <CornerMark />
              {/* Faction header */}
              <div className="flex items-center gap-2 mb-1">
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ backgroundColor: faction.color }}
                />
                <span className="font-mono text-base text-hud-text truncate">
                  {faction.name}
                </span>
                <span className="font-mono text-sm text-hud-muted ml-auto">
                  {faction.agent_count}
                </span>
              </div>

              {/* Power bar */}
              <div className="h-1 bg-void rounded-full overflow-hidden mb-1">
                <div
                  className="h-full rounded-full transition-all"
                  style={{
                    width: `${power}%`,
                    backgroundColor: faction.color + "80",
                  }}
                />
              </div>

              {/* Agent list (shown when selected) */}
              {isSelected && factionAgents.length > 0 && (
                <div className="mt-2 space-y-0.5">
                  {factionAgents.map((agent) => (
                    <button
                      key={agent.id}
                      className="w-full text-left px-1 py-0.5 text-[13px] font-mono text-hud-muted hover:text-hud-text transition-colors truncate"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedAgent(agent.id);
                        setIntelTab("agent");
                      }}
                    >
                      › {agent.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Relationship matrix */}
      {displayFactions.length > 1 && factions.length > 0 && (
        <div className="border-t border-hud-border p-2">
          <div className="font-mono text-sm uppercase tracking-[0.15em] text-hud-label mb-2">
            RELATIONS
          </div>
          <div className="grid gap-px" style={{ gridTemplateColumns: `auto repeat(${displayFactions.length}, 1fr)` }}>
            {/* Header row */}
            <div />
            {displayFactions.map((f) => (
              <div
                key={f.id}
                className="text-[11px] font-mono text-center truncate px-0.5"
                style={{ color: f.color }}
              >
                {f.name.slice(0, 3)}
              </div>
            ))}
            {/* Matrix rows */}
            {displayFactions.map((fA) => (
              <div key={fA.id} className="contents">
                <div
                  className="text-[11px] font-mono truncate pr-1"
                  style={{ color: fA.color }}
                >
                  {fA.name.slice(0, 3)}
                </div>
                {displayFactions.map((fB) => {
                  if (fA.id === fB.id) {
                    return <div key={fB.id} className="w-full aspect-square bg-hud-border/30" />;
                  }
                  const rel = getRelationType(fA.id, fB.id);
                  return (
                    <div
                      key={fB.id}
                      className="w-full aspect-square rounded-sm"
                      style={{
                        backgroundColor: rel ? typeColor[rel] + "40" : "#1a1a2e30",
                      }}
                      title={rel || "unknown"}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

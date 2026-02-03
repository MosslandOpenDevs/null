"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import { useLocale } from "next-intl";
import { useSimulationStore } from "@/stores/simulation";
import { AgentAvatar } from "./AgentAvatar";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

export function SystemPulse() {
  const locale = useLocale();
  const {
    world,
    factions,
    agents,
    events,
    selectedFaction,
    setSelectedFaction,
    setSelectedAgent,
    setIntelTab,
  } = useSimulationStore();

  // Derive factions from config if API factions are empty
  const displayFactions =
    factions.length > 0
      ? factions
      : (
          (world?.config as Record<string, unknown>)?.factions as Array<
            Record<string, unknown>
          > || []
        ).map((f, i) => ({
          id: String(i),
          world_id: world?.id || "",
          name: String(f.name || ""),
          description: String(f.description || ""),
          color: String(f.color || "#6366f1"),
          agent_count: Number(f.agent_count || 0),
        }));

  // Agent/faction lookup for mini feed
  const agentMap = useMemo(() => new Map(agents.map((a) => [a.id, a])), [agents]);
  const factionMap = useMemo(() => new Map(factions.map((f) => [f.id, f])), [factions]);

  const getFactionColor = useCallback(
    (agentId: string): string => {
      const agent = agentMap.get(agentId);
      if (!agent?.faction_id) return "#6366f1";
      const faction = factionMap.get(agent.faction_id);
      return faction?.color || "#6366f1";
    },
    [agentMap, factionMap]
  );

  // Fetch initial messages from API on mount
  const [initialMessages, setInitialMessages] = useState<
    Array<{ agent_id: string; agent_name: string; content: string; content_ko?: string }>
  >([]);

  useEffect(() => {
    if (!world) return;
    fetch(`${API_URL}/api/worlds/${world.id}/recent-messages?limit=5`)
      .then((r) => (r.ok ? r.json() : []))
      .then(setInitialMessages)
      .catch(() => {});
  }, [world?.id]);

  // Recent messages: merge initial API data + live WebSocket events (last 5)
  const recentMessages = useMemo(() => {
    const msgs: Array<{
      id: string;
      agentName: string;
      content: string;
      color: string;
      agentId: string;
    }> = [];
    const pick = (en: string, ko?: string) => (locale === "ko" && ko) ? ko : en;

    // First add from live events
    for (let i = events.length - 1; i >= 0 && msgs.length < 5; i--) {
      const ev = events[i];
      if (ev.type === "agent.message") {
        const agentId = ev.payload.agent_id as string;
        const agent = agentMap.get(agentId);
        msgs.push({
          id: `${ev.timestamp}-${agentId}`,
          agentName: agent?.name || (ev.payload.agent_name as string) || "Unknown",
          content: ev.payload.content as string,
          color: getFactionColor(agentId),
          agentId,
        });
      }
    }

    // If not enough from live events, fill from API initial data
    if (msgs.length < 5 && initialMessages.length > 0) {
      for (const msg of initialMessages) {
        if (msgs.length >= 5) break;
        if (msgs.some((m) => m.content === msg.content)) continue;
        msgs.push({
          id: `init-${msg.agent_id}-${msg.content.slice(0, 20)}`,
          agentName: msg.agent_name || agentMap.get(msg.agent_id)?.name || "Unknown",
          content: pick(msg.content, msg.content_ko),
          color: getFactionColor(msg.agent_id),
          agentId: msg.agent_id,
        });
      }
    }

    return msgs;
  }, [events, agentMap, getFactionColor, initialMessages, locale]);

  return (
    <div className="flex flex-col h-full bg-void-light border-l border-hud-border w-[320px] min-w-[320px] overflow-hidden">
      {/* FACTION ACCORDION */}
      <div className="border-b border-hud-border">
        <div className="px-3 py-2 border-b border-hud-border">
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-hud-label">
            FACTIONS
          </span>
        </div>
        <div className="max-h-[220px] overflow-y-auto p-1.5 space-y-1">
          {displayFactions.map((faction) => {
            const isOpen = selectedFaction === faction.id;
            const factionAgents =
              factions.length > 0
                ? agents.filter((a) => a.faction_id === faction.id).slice(0, 3)
                : [];
            return (
              <div
                key={faction.id}
                className="border border-hud-border cursor-pointer transition-colors hover:border-hud-border-active"
                style={{
                  borderColor: isOpen ? faction.color + "60" : undefined,
                  backgroundColor: isOpen ? faction.color + "08" : undefined,
                }}
              >
                <button
                  className="w-full flex items-center gap-2 px-2 py-1.5"
                  onClick={() => setSelectedFaction(isOpen ? null : faction.id)}
                >
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: faction.color }}
                  />
                  <span className="font-mono text-xs text-hud-text truncate flex-1 text-left">
                    {faction.name}
                  </span>
                  <span className="font-mono text-[11px] text-hud-muted">
                    {faction.agent_count}
                  </span>
                </button>
                {isOpen && factionAgents.length > 0 && (
                  <div className="px-2 pb-1.5 space-y-0.5">
                    {factionAgents.map((agent) => (
                      <button
                        key={agent.id}
                        className="w-full text-left px-1 py-0.5 text-[11px] font-mono text-hud-muted hover:text-hud-text transition-colors truncate"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedAgent(agent.id);
                          setIntelTab("agent");
                        }}
                      >
                        &rsaquo; {agent.name}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* MINI LIVE FEED */}
      <div className="border-b border-hud-border flex-1 min-h-0">
        <div className="px-3 py-2 border-b border-hud-border">
          <span className="font-mono text-xs uppercase tracking-[0.2em] text-hud-label">
            RECENT ACTIVITY
          </span>
        </div>
        <div className="p-2 space-y-1.5 overflow-hidden">
          {recentMessages.length === 0 && (
            <div className="font-mono text-[11px] text-hud-muted animate-pulse py-2 text-center">
              AWAITING TRANSMISSION
            </div>
          )}
          {recentMessages.map((msg) => (
            <div key={msg.id} className="flex items-start gap-1.5 text-xs leading-tight">
              <AgentAvatar name={msg.agentName} factionColor={msg.color} size="sm" />
              <div className="flex-1 min-w-0">
                <button
                  onClick={() => {
                    setSelectedAgent(msg.agentId);
                    setIntelTab("agent");
                  }}
                  className="hover:underline font-semibold font-sans text-xs"
                  style={{ color: msg.color }}
                >
                  {msg.agentName}
                </button>
                <span className="text-hud-text font-sans text-xs line-clamp-1 block">{msg.content}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* WORLD STATUS */}
      <div className="px-3 py-3">
        <div className="font-mono text-xs uppercase tracking-[0.2em] text-hud-label mb-2">
          WORLD STATUS
        </div>
        <div className="grid grid-cols-2 gap-2">
          <StatusItem label="STATUS" value={world?.status?.toUpperCase() || "—"} />
          <StatusItem label="EPOCH" value={String(world?.current_epoch ?? 0)} />
          <StatusItem label="AGENTS" value={String(agents.length)} />
          <StatusItem label="FACTIONS" value={String(displayFactions.length)} />
        </div>
      </div>
    </div>
  );
}

function StatusItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[11px] text-hud-label uppercase">{label}</div>
      <div className="font-mono text-xs text-accent">{value}</div>
    </div>
  );
}

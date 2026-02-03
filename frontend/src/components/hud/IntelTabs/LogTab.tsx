"use client";

import { useState } from "react";
import { useLocale } from "next-intl";
import { useSimulationStore } from "@/stores/simulation";
import { AgentAvatar } from "@/components/AgentAvatar";

const EVENT_TYPES = [
  "all",
  "agent.message",
  "agent.state",
  "epoch.transition",
  "event.triggered",
  "consensus.reached",
  "wiki.edit",
  "herald.announcement",
  "relation.update",
] as const;

const TYPE_COLOR: Record<string, string> = {
  "agent.message": "text-hud-text",
  "agent.state": "text-hud-muted",
  "epoch.transition": "text-accent",
  "event.triggered": "text-warning",
  "consensus.reached": "text-cyan",
  "wiki.edit": "text-success",
  "herald.announcement": "text-herald",
  "relation.update": "text-hud-muted",
};

function useCopy() {
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const copy = async (text: string, idx: number) => {
    await navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 1200);
  };
  return { copiedIdx, copy };
}

export function LogTab() {
  const locale = useLocale();
  const { events, agents, factions } = useSimulationStore();
  const [filter, setFilter] = useState<string>("all");
  const { copiedIdx, copy } = useCopy();

  const filtered = filter === "all"
    ? events
    : events.filter((e) => e.type === filter);

  // Show most recent first
  const displayed = [...filtered].reverse().slice(0, 100);

  return (
    <div className="flex flex-col h-full">
      {/* Filter bar */}
      <div className="flex flex-wrap gap-1 p-2 border-b border-hud-border">
        {EVENT_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type)}
            className={`font-mono text-xs uppercase px-1.5 py-0.5 border transition-colors ${
              filter === type
                ? "border-accent text-accent"
                : "border-hud-border text-hud-muted hover:text-hud-text"
            }`}
          >
            {type === "all" ? "ALL" : type.split(".")[1]}
          </button>
        ))}
      </div>

      {/* Log entries */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {displayed.length === 0 && (
          <div className="font-mono text-xs text-hud-label text-center py-4">
            NO EVENTS
          </div>
        )}
        {displayed.map((event, i) => {
          const time = new Date(event.timestamp).toLocaleTimeString("en-US", {
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });
          const summary = getSummary(event, locale);

          return (
            <div
              key={i}
              className="font-mono text-xs flex gap-2 group cursor-pointer hover:bg-accent/5"
              onClick={() => copy(`[${time}] ${event.type}: ${summary}`, i)}
            >
              {event.type === "agent.message" && (() => {
                const agentId = event.payload.agent_id as string;
                const agent = agents.find(a => a.id === agentId);
                const faction = agent?.faction_id ? factions.find(f => f.id === agent.faction_id) : null;
                return <AgentAvatar name={agent?.name || "?"} factionColor={faction?.color} size="sm" />;
              })()}
              <span className="text-hud-label flex-shrink-0 w-[52px]">{time}</span>
              <span className={`flex-shrink-0 w-[60px] truncate ${TYPE_COLOR[event.type] || "text-hud-muted"}`}>
                {event.type.split(".")[1]}
              </span>
              <span className="text-hud-muted truncate flex-1">{summary}</span>
              <span className="text-xs text-hud-label opacity-0 group-hover:opacity-100 flex-shrink-0">
                {copiedIdx === i ? "COPIED" : "📋"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function getSummary(event: { type: string; payload: Record<string, unknown> }, locale: string = "en"): string {
  const p = event.payload;
  switch (event.type) {
    case "agent.message": {
      const content = (locale === "ko" && p.content_ko) ? String(p.content_ko) : String(p.content || "");
      return `${p.agent_name || "Agent"}: ${content.slice(0, 60)}`;
    }
    case "agent.state":
      return `${p.agent_name || "Agent"} → ${p.status}`;
    case "epoch.transition":
      return `Epoch ${p.epoch}`;
    case "event.triggered":
      return String(p.description || p.text || "Event");
    case "consensus.reached":
      return String(p.claim || "Agreement reached");
    case "wiki.edit":
      return `${p.title || "Page"} updated`;
    case "herald.announcement":
      return String(p.text || "").slice(0, 60);
    case "relation.update":
      return `${p.type}: ${p.agent_a_name || "?"} ↔ ${p.agent_b_name || "?"}`;
    default:
      return JSON.stringify(p).slice(0, 60);
  }
}

"use client";

import { useState } from "react";
import { useSimulationStore } from "@/stores/simulation";
import { AgentAvatar } from "@/components/AgentAvatar";

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button
      onClick={handleCopy}
      className="font-mono text-base px-1.5 py-0.5 border border-hud-border text-hud-muted hover:text-accent hover:border-accent transition-colors"
      title="Copy agent profile as JSON"
    >
      {copied ? "COPIED" : "📋 JSON"}
    </button>
  );
}

export function AgentTab() {
  const { selectedAgent, agents, events, relationships, factions } = useSimulationStore();
  const agent = agents.find((a) => a.id === selectedAgent);

  if (!agent) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-mono text-base text-hud-muted">
          SELECT AN AGENT TO INSPECT
        </span>
      </div>
    );
  }

  const faction = factions.find((f) => f.id === agent.faction_id);

  // Recent messages from this agent
  const agentMessages = events
    .filter((e) => e.type === "agent.message" && e.payload.agent_id === selectedAgent)
    .slice(-8);

  // Agent relationships
  const agentRels = relationships.filter(
    (r) => r.agent_a === agent.id || r.agent_b === agent.id
  );

  const relTypeColor: Record<string, string> = {
    ally: "text-success",
    rival: "text-danger",
    neutral: "text-hud-muted",
    trade: "text-cyan",
    mentor: "text-accent",
  };

  const agentJson = JSON.stringify({
    id: agent.id,
    name: agent.name,
    faction: faction?.name || null,
    persona: agent.persona,
    beliefs: agent.beliefs,
    status: agent.status,
  }, null, 2);

  return (
    <div className="p-3 space-y-4">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AgentAvatar name={agent.name} factionColor={faction?.color} size="md" />
            <h3 className="font-sans text-lg font-semibold text-hud-text">{agent.name}</h3>
          </div>
          <CopyButton text={agentJson} />
        </div>
        <div className="font-mono text-sm text-hud-muted mt-0.5">
          {faction?.name && <span style={{ color: faction.color }}>{faction.name}</span>}
          {faction?.name && " · "}
          {agent.persona.role as string}
        </div>
        <div className="font-mono text-base text-hud-label mt-0.5 uppercase">
          STATUS: {agent.status}
        </div>
      </div>

      {/* Persona */}
      <div className="space-y-3">
        <InfoSection label="PERSONALITY" value={agent.persona.personality as string} />
        <InfoSection label="MOTIVATION" value={agent.persona.motivation as string} />
        <InfoSection label="SECRET" value={agent.persona.secret as string} />
        <InfoSection label="SPEECH STYLE" value={agent.persona.speech_style as string} />
      </div>

      {/* Beliefs */}
      <div>
        <div className="font-mono text-base uppercase tracking-[0.15em] text-hud-label mb-1">
          BELIEFS
        </div>
        {agent.beliefs.length > 0 ? (
          <ul className="space-y-0.5">
            {agent.beliefs.map((b, i) => (
              <li key={i} className="font-mono text-sm text-hud-muted">
                • {String(b)}
              </li>
            ))}
          </ul>
        ) : (
          <div className="font-mono text-sm text-hud-label">No beliefs recorded</div>
        )}
      </div>

      {/* Relationships */}
      {agentRels.length > 0 && (
        <div>
          <div className="font-mono text-base uppercase tracking-[0.15em] text-hud-label mb-1">
            RELATIONSHIPS
          </div>
          <div className="space-y-0.5">
            {agentRels.slice(0, 10).map((rel) => {
              const otherId = rel.agent_a === agent.id ? rel.agent_b : rel.agent_a;
              const other = agents.find((a) => a.id === otherId);
              return (
                <div key={rel.id} className="font-mono text-sm flex items-center gap-2">
                  <span className={relTypeColor[rel.type] || "text-hud-muted"}>
                    {rel.type.toUpperCase()}
                  </span>
                  <span className="text-hud-text">{other?.name || "Unknown"}</span>
                  <span className="text-hud-label ml-auto">{(rel.strength * 100).toFixed(0)}%</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent messages */}
      <div>
        <div className="font-mono text-base uppercase tracking-[0.15em] text-hud-label mb-1">
          RECENT TRANSMISSIONS
        </div>
        <div className="space-y-1">
          {agentMessages.map((e, i) => (
            <div key={i} className="flex gap-2 items-start">
              <AgentAvatar name={agent.name} factionColor={faction?.color} size="sm" />
              <div className="font-sans text-base text-hud-muted bg-void/50 p-2 border border-hud-border rounded flex-1"
                style={{ borderLeft: `3px solid ${faction?.color || "#6366f1"}40` }}>
                {e.payload.content as string}
              </div>
            </div>
          ))}
          {agentMessages.length === 0 && (
            <div className="font-mono text-sm text-hud-label">No transmissions yet</div>
          )}
        </div>
      </div>
    </div>
  );
}

function InfoSection({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div>
      <div className="font-mono text-base uppercase tracking-[0.15em] text-hud-label mb-0.5">
        {label}
      </div>
      <div className="font-sans text-base text-hud-muted leading-relaxed">{value}</div>
    </div>
  );
}

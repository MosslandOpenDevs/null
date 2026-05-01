"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useSimulationStore } from "@/stores/simulation";
import { AgentAvatar } from "@/components/AgentAvatar";

export function OraclePanel() {
  const {
    oracleOpen,
    oracleTarget,
    closeOracle,
    agents,
    factions,
    relationships,
    wikiPages,
    events,
  } = useSimulationStore();

  const panelRef = useRef<HTMLDivElement>(null);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && oracleOpen) closeOracle();
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [oracleOpen, closeOracle]);

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (oracleOpen && panelRef.current && !panelRef.current.contains(e.target as Node)) {
        closeOracle();
      }
    };
    window.addEventListener("mousedown", handleClick);
    return () => window.removeEventListener("mousedown", handleClick);
  }, [oracleOpen, closeOracle]);

  const renderContent = () => {
    if (!oracleTarget) return null;

    switch (oracleTarget.type) {
      case "agent": {
        const agent = agents.find((a) => a.id === oracleTarget.id);
        if (!agent) return <EmptyContent text="Agent not found" />;

        const faction = factions.find((f) => f.id === agent.faction_id);
        const agentRels = relationships.filter(
          (r) => r.agent_a === agent.id || r.agent_b === agent.id
        );
        const agentMessages = events
          .filter((e) => e.type === "agent.message" && e.payload.agent_id === agent.id)
          .slice(-8);

        return (
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <AgentAvatar name={agent.name} factionColor={faction?.color} size="md" />
                <h3 className="font-sans text-lg font-semibold text-hud-text">{agent.name}</h3>
              </div>
              <div className="font-mono text-sm text-hud-muted mt-0.5">
                {faction && <span style={{ color: faction.color }}>{faction.name}</span>}
                {faction && " · "}
                {agent.persona.role as string}
              </div>
              <div className="font-mono text-[11px] text-hud-label mt-0.5 uppercase">
                STATUS: {agent.status}
              </div>
            </div>

            <InfoSection label="PERSONALITY" value={agent.persona.personality as string} />
            <InfoSection label="MOTIVATION" value={agent.persona.motivation as string} />
            <InfoSection label="SECRET" value={agent.persona.secret as string} />

            {agent.beliefs.length > 0 && (
              <div>
                <SectionLabel>BELIEFS</SectionLabel>
                <ul className="space-y-0.5">
                  {agent.beliefs.map((b, i) => (
                    <li key={i} className="font-mono text-sm text-hud-muted">• {String(b)}</li>
                  ))}
                </ul>
              </div>
            )}

            {agentRels.length > 0 && (
              <div>
                <SectionLabel>RELATIONSHIPS</SectionLabel>
                <div className="space-y-0.5">
                  {agentRels.slice(0, 10).map((rel) => {
                    const otherId = rel.agent_a === agent.id ? rel.agent_b : rel.agent_a;
                    const other = agents.find((a) => a.id === otherId);
                    return (
                      <div key={rel.id} className="font-mono text-sm flex items-center gap-2">
                        <span className={
                          rel.strength > 0.3 ? "text-success" :
                          rel.strength < -0.3 ? "text-danger" : "text-hud-muted"
                        }>
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

            {agentMessages.length > 0 && (
              <div>
                <SectionLabel>RECENT TRANSMISSIONS</SectionLabel>
                <div className="space-y-1">
                  {agentMessages.map((e, i) => (
                    <div key={i} className="font-sans text-sm text-hud-muted p-2 border border-hud-border/50 rounded-sm"
                      style={{ borderLeft: `3px solid ${faction?.color || "#6366f1"}40` }}>
                      {e.payload.content as string}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      }

      case "wiki": {
        const page = wikiPages.find((p) => p.id === oracleTarget.id);
        if (!page) return <EmptyContent text="Wiki page not found" />;

        return (
          <div className="space-y-3">
            <h3 className="font-serif text-xl text-hud-text font-semibold">{page.title}</h3>
            <div className="flex gap-2 font-mono text-[11px] text-hud-label uppercase">
              <span className={
                page.status === "canon" ? "text-success" :
                page.status === "disputed" ? "text-danger" : "text-hud-muted"
              }>
                {page.status}
              </span>
              <span>v{page.version}</span>
            </div>
            <div className="font-serif text-base text-hud-text leading-relaxed whitespace-pre-wrap">
              {page.content}
            </div>
          </div>
        );
      }

      case "faction": {
        const faction = factions.find((f) => f.id === oracleTarget.id);
        if (!faction) return <EmptyContent text="Faction not found" />;

        const factionAgents = agents.filter((a) => a.faction_id === faction.id);

        return (
          <div className="space-y-3">
            <div>
              <h3 className="font-sans text-lg font-semibold" style={{ color: faction.color }}>
                {faction.name}
              </h3>
              <p className="font-sans text-sm text-hud-muted mt-1">{faction.description}</p>
            </div>
            <div>
              <SectionLabel>MEMBERS ({factionAgents.length})</SectionLabel>
              <div className="space-y-1">
                {factionAgents.map((a) => (
                  <div key={a.id} className="flex items-center gap-2">
                    <AgentAvatar name={a.name} factionColor={faction.color} size="sm" />
                    <span className="font-mono text-sm text-hud-text">{a.name}</span>
                    <span className="font-mono text-[10px] text-hud-label ml-auto">{a.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      }

      case "event": {
        const event = events.find(
          (e) =>
            (e.type === "event.triggered" || e.type === "herald.announcement") &&
            e.timestamp === oracleTarget.id
        );
        if (!event) return <EmptyContent text="Event not found" />;

        return (
          <div className="space-y-3">
            <SectionLabel>EVENT</SectionLabel>
            <p className="font-sans text-base text-hud-text">
              {(event.payload.description as string) || (event.payload.text as string) || "Event occurred"}
            </p>
            <div className="font-mono text-[11px] text-hud-label">
              Epoch {event.epoch}
            </div>
          </div>
        );
      }

      default:
        return null;
    }
  };

  return (
    <AnimatePresence>
      {oracleOpen && (
        <motion.div
          ref={panelRef}
          initial={{ x: "100%" }}
          animate={{ x: 0 }}
          exit={{ x: "100%" }}
          transition={{ type: "spring", damping: 25, stiffness: 200 }}
          className="fixed top-0 right-0 h-screen w-80 lg:w-96 z-50 backdrop-blur-xl bg-void/80 border-l border-hud-border overflow-y-auto"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-hud-border sticky top-0 bg-void/90 backdrop-blur-sm z-10">
            <span className="font-mono text-[13px] uppercase tracking-[0.2em] text-hud-label">
              ORACLE
            </span>
            <button
              onClick={closeOracle}
              className="font-mono text-sm text-hud-muted hover:text-hud-text transition-colors"
            >
              ✕
            </button>
          </div>

          {/* Content */}
          <div className="p-4">
            {renderContent()}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-mono text-[11px] uppercase tracking-[0.15em] text-hud-label mb-1">
      {children}
    </div>
  );
}

function InfoSection({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div>
      <SectionLabel>{label}</SectionLabel>
      <div className="font-sans text-sm text-hud-muted leading-relaxed">{value}</div>
    </div>
  );
}

function EmptyContent({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-center h-32">
      <span className="font-mono text-sm text-hud-muted">{text}</span>
    </div>
  );
}

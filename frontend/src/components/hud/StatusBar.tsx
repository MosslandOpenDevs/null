"use client";

import { useState } from "react";
import { useSimulationStore } from "@/stores/simulation";
import { ExportPanel } from "@/components/ExportPanel";

export function StatusBar() {
  const { world, agents, events } = useSimulationStore();
  const [exportOpen, setExportOpen] = useState(false);

  if (!world) return null;

  const worldName =
    (world.config as Record<string, unknown>)?.description
      ? String((world.config as Record<string, unknown>).description).slice(0, 40)
      : world.seed_prompt.slice(0, 40);

  const activeConversations = events
    .filter((e) => e.type === "agent.message")
    .slice(-20).length;

  const isLive = world.status === "running";

  return (
    <>
      <div className="relative h-8 flex items-center justify-between px-4 bg-void-light border-b border-hud-border font-mono text-sm uppercase tracking-[0.2em] text-hud-muted overflow-hidden scanline-sweep">
        <div className="flex items-center gap-6">
          <span className="text-hud-label">WORLD:</span>
          <span className="text-hud-text truncate max-w-[200px]">{worldName}</span>
          <span className="text-hud-label">EPOCH:</span>
          <span className="text-hud-text">{String(world.current_epoch).padStart(2, "0")}</span>
          <span className="text-hud-label">TICK:</span>
          <span className="text-hud-text">{String(world.current_tick).padStart(2, "0")}</span>
        </div>
        <div className="flex items-center gap-6">
          <span className="text-hud-label">AGENTS:</span>
          <span className="text-hud-text">{agents.length}</span>
          <span className="text-hud-label">FEED:</span>
          <span className="text-hud-text">{activeConversations}</span>
          <button
            onClick={() => setExportOpen(true)}
            className="text-hud-muted hover:text-accent transition-colors border border-hud-border hover:border-accent px-2 py-0.5"
          >
            EXPORT
          </button>
          <span className={`flex items-center gap-1 ${isLive ? "text-success" : "text-hud-muted"}`}>
            <span className={`inline-block w-1.5 h-1.5 rounded-full ${isLive ? "bg-success animate-pulse-glow" : "bg-hud-muted"}`} />
            {isLive ? "LIVE" : world.status.toUpperCase()}
          </span>
        </div>
      </div>
      <ExportPanel open={exportOpen} onClose={() => setExportOpen(false)} />
    </>
  );
}

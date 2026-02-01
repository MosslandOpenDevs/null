"use client";

import { useEffect } from "react";
import { useSimulationStore } from "@/stores/simulation";
import { useMultiverseStore, ResonanceLink } from "@/stores/multiverse";

export function ResonanceTab() {
  const { world } = useSimulationStore();
  const { resonanceLinks, fetchResonance } = useMultiverseStore();

  useEffect(() => {
    if (world?.id) {
      fetchResonance(world.id);
    }
  }, [world?.id, fetchResonance]);

  if (!world) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-mono text-[11px] text-hud-muted">NO WORLD SELECTED</span>
      </div>
    );
  }

  if (resonanceLinks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 p-4">
        <span className="font-mono text-[11px] text-hud-muted text-center">
          NO RESONANCE DETECTED
        </span>
        <span className="font-mono text-[9px] text-hud-label text-center">
          Resonance links appear when similar concepts are found across different worlds.
          Run multiple simulations to discover cross-world connections.
        </span>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-hud-label">
        CROSS-WORLD RESONANCE ({resonanceLinks.length})
      </div>

      <div className="space-y-2">
        {resonanceLinks.map((link: ResonanceLink) => {
          const isWorldA = link.world_a === world.id;
          const otherWorldId = isWorldA ? link.world_b : link.world_a;
          const strengthPct = (link.strength * 100).toFixed(0);

          return (
            <div
              key={link.id}
              className="p-2 border border-hud-border hover:border-accent/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[10px] text-accent">
                  {link.entity_type.toUpperCase()}
                </span>
                <span className="font-mono text-[9px] text-herald">
                  {strengthPct}% match
                </span>
              </div>
              <div className="font-mono text-[9px] text-hud-muted mt-1">
                World: {otherWorldId.slice(0, 8)}…
              </div>
              <div className="w-full bg-void h-1 mt-1.5">
                <div
                  className="h-full bg-accent/60"
                  style={{ width: `${strengthPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

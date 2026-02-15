"use client";

import { useEffect, useMemo } from "react";
import { useSimulationStore } from "@/stores/simulation";
import { useMultiverseStore, type WorldNeighbor } from "@/stores/multiverse";

export function ResonanceTab() {
  const { world } = useSimulationStore();
  const { worldNeighbors, worldsMap, fetchWorldNeighbors, fetchWorldMap } = useMultiverseStore();

  useEffect(() => {
    if (world?.id) {
      fetchWorldNeighbors(world.id, 0.3);
      fetchWorldMap(0.3, 2);
    }
  }, [world?.id, fetchWorldNeighbors, fetchWorldMap]);

  const worldNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const node of worldsMap?.worlds || []) {
      map.set(node.id, node.seed_prompt);
    }
    return map;
  }, [worldsMap]);

  if (!world) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-mono text-base text-hud-muted">NO WORLD SELECTED</span>
      </div>
    );
  }

  if (worldNeighbors.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 p-4">
        <span className="font-mono text-base text-hud-muted text-center">
          NO RESONANCE DETECTED
        </span>
        <span className="font-mono text-sm text-hud-label text-center">
          Resonance links appear when similar concepts are found across different worlds.
          Run multiple simulations to discover cross-world connections.
        </span>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      {worldsMap && worldsMap.links.length > 0 && (
        <div className="p-2 border border-hud-border/60 bg-void">
          <div className="font-mono text-sm uppercase tracking-[0.15em] text-hud-label mb-2">
            WORLD MAP LINKS ({worldsMap.links.length})
          </div>
          <div className="space-y-1">
            {worldsMap.links.slice(0, 5).map((link, idx) => {
              const a = worldNameById.get(link.world_a) || `${link.world_a.slice(0, 8)}…`;
              const b = worldNameById.get(link.world_b) || `${link.world_b.slice(0, 8)}…`;
              return (
                <div key={`${link.world_a}-${link.world_b}-${idx}`} className="font-mono text-sm text-hud-muted">
                  {a} ↔ {b} ({(link.strength * 100).toFixed(0)}%, {link.count})
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="font-mono text-sm uppercase tracking-[0.15em] text-hud-label">
        WORLD NEIGHBORS ({worldNeighbors.length})
      </div>

      <div className="space-y-2">
        {worldNeighbors.map((neighbor: WorldNeighbor) => {
          const strengthPct = (neighbor.strength * 100).toFixed(0);

          return (
            <div
              key={neighbor.world_id}
              className="p-2 border border-hud-border hover:border-accent/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-[13px] text-accent uppercase">
                  {neighbor.status}
                </span>
                <span className="font-mono text-sm text-herald">
                  {strengthPct}% match
                </span>
              </div>
              <div className="font-sans text-sm text-hud-text mt-1 truncate">
                {neighbor.seed_prompt}
              </div>
              <div className="font-mono text-sm text-hud-muted mt-1">
                Links: {neighbor.resonance_count}
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

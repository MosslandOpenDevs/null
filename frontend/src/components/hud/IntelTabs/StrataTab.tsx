"use client";

import { useSimulationStore } from "@/stores/simulation";
import { StrataTimeline } from "@/components/StrataTimeline";

export function StrataTab() {
  const { world } = useSimulationStore();

  if (!world) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-mono text-[11px] text-hud-muted">
          NO WORLD LOADED
        </span>
      </div>
    );
  }

  return <StrataTimeline worldId={world.id} />;
}

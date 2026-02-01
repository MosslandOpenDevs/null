"use client";

import { useSimulationStore } from "@/stores/simulation";

const EPOCH_COLORS = [
  "#6366f1", "#8b5cf6", "#a855f7", "#d946ef",
  "#ec4899", "#f43f5e", "#ef4444", "#f97316",
  "#f59e0b", "#eab308", "#84cc16", "#22c55e",
];

export function TimelineRibbon() {
  const { world, events } = useSimulationStore();
  if (!world) return null;

  const totalEpochs = Math.max(world.current_epoch + 1, 1);

  // Find key events per epoch
  const epochEvents = new Map<number, string[]>();
  for (const e of events) {
    if (e.type === "event.triggered" || e.type === "herald.announcement") {
      const list = epochEvents.get(e.epoch) || [];
      list.push(
        (e.payload.description as string) || (e.payload.text as string) || "Event"
      );
      epochEvents.set(e.epoch, list);
    }
  }

  return (
    <div className="bg-void-light border-t border-hud-border">
      <div className="flex h-7 items-stretch">
        {Array.from({ length: totalEpochs }, (_, i) => {
          const color = EPOCH_COLORS[i % EPOCH_COLORS.length];
          const isCurrent = i === world.current_epoch;
          const width = `${100 / Math.max(totalEpochs, 1)}%`;
          const evts = epochEvents.get(i);

          return (
            <div
              key={i}
              className="relative flex items-center justify-center font-mono text-[9px] transition-all cursor-pointer hover:brightness-125 group"
              style={{
                width,
                backgroundColor: color + (isCurrent ? "25" : "10"),
                borderRight: "1px solid #1a1a2e",
              }}
              title={evts ? evts.join("\n") : undefined}
            >
              <span className="text-hud-muted">E{i}</span>
              {/* Event markers */}
              {evts && evts.length > 0 && (
                <span
                  className="absolute top-1 right-1 w-1 h-1 rounded-full"
                  style={{ backgroundColor: color }}
                />
              )}
              {isCurrent && (
                <div
                  className="absolute bottom-0 left-0 right-0 h-0.5"
                  style={{ backgroundColor: color }}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Tick progress */}
      <div className="h-0.5 bg-void">
        <div
          className="h-full bg-accent/40 transition-all"
          style={{
            width: `${((world.current_tick || 0) / 10) * 100}%`,
          }}
        />
      </div>
    </div>
  );
}

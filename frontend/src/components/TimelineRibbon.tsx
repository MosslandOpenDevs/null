"use client";

import { useRef, useState, useCallback } from "react";
import { useSimulationStore } from "@/stores/simulation";

const THEME_COLORS: Record<string, string> = {
  prosperity: "#33ff88",
  conflict: "#ff4466",
  discovery: "#ffaa33",
  transition: "#a855f7",
};

const EPOCH_COLORS = [
  "#4f46e5", "#7c3aed", "#9333ea", "#c026d3",
  "#db2777", "#e11d48", "#dc2626", "#ea580c",
  "#d97706", "#ca8a04", "#65a30d", "#059669",
];

export function TimelineRibbon() {
  const { world, events, chronicleItems } = useSimulationStore();
  const ribbonRef = useRef<HTMLDivElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleMouseDown = useCallback(() => setIsDragging(true), []);
  const handleMouseUp = useCallback(() => setIsDragging(false), []);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging || !ribbonRef.current || !world) return;
      const rect = ribbonRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const ratio = x / rect.width;
      const targetEpoch = Math.floor(ratio * (world.current_epoch + 1));

      // Scroll chronicle to epoch divider
      const epochItem = chronicleItems.find(
        (item) => item.type === "epoch" && item.epoch === targetEpoch
      );
      if (epochItem) {
        const el = document.getElementById(`chronicle-${epochItem.id}`);
        el?.scrollIntoView({ behavior: "smooth" });
      }
    },
    [isDragging, world, chronicleItems]
  );

  if (!world) return null;

  const totalEpochs = Math.max(world.current_epoch + 1, 1);

  // Find events per epoch
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

  // Detect epoch themes from strata
  const getEpochColor = (epoch: number): string => {
    const epochItem = chronicleItems.find(
      (item) => item.type === "epoch" && item.epoch === epoch
    );
    if (epochItem?.type === "epoch" && epochItem.dominantTheme) {
      return THEME_COLORS[epochItem.dominantTheme] || EPOCH_COLORS[epoch % EPOCH_COLORS.length];
    }
    return EPOCH_COLORS[epoch % EPOCH_COLORS.length];
  };

  return (
    <div className="bg-void-light border-t border-hud-border">
      <div
        ref={ribbonRef}
        className="flex h-[60px] items-stretch cursor-crosshair select-none"
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onMouseMove={handleMouseMove}
      >
        {Array.from({ length: totalEpochs }, (_, i) => {
          const color = getEpochColor(i);
          const isCurrent = i === world.current_epoch;
          const width = `${100 / Math.max(totalEpochs, 1)}%`;
          const evts = epochEvents.get(i);

          return (
            <div
              key={i}
              className="relative flex flex-col items-center justify-center font-mono text-sm transition-all hover:brightness-125 group"
              style={{
                width,
                backgroundColor: color + (isCurrent ? "18" : "08"),
                borderRight: "1px solid #2a2a3a",
              }}
              title={evts ? evts.join("\n") : `Epoch ${i}`}
            >
              <span className="text-hud-muted text-[11px]">E{i}</span>
              {/* Event markers */}
              {evts && evts.length > 0 && (
                <div className="flex gap-0.5 mt-1">
                  {evts.slice(0, 3).map((_, j) => (
                    <span
                      key={j}
                      className="w-1.5 h-1.5 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                  {evts.length > 3 && (
                    <span className="text-[8px] text-hud-label">+{evts.length - 3}</span>
                  )}
                </div>
              )}
              {/* Current epoch indicator */}
              {isCurrent && (
                <div
                  className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0.5 h-full"
                  style={{ backgroundColor: color + "60" }}
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

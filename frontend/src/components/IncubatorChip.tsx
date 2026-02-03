"use client";

import { WorldData } from "@/stores/simulation";

interface IncubatorChipProps {
  world: WorldData;
  locale: string;
}

export function IncubatorChip({ world, locale }: IncubatorChipProps) {
  const progress = (world.config as Record<string, unknown>)?._genesis_progress as
    | { percent: number; step_num: number; total_steps: number }
    | undefined;

  const statusLabel =
    world.status === "generating"
      ? progress
        ? `STEP ${progress.step_num}/${progress.total_steps}`
        : "GENERATING..."
      : world.status === "running"
      ? `EPOCH ${world.current_epoch}`
      : world.status.toUpperCase();

  return (
    <a
      href={`/${locale}/world/${world.id}`}
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded border border-hud-border bg-void-light/40 hover:border-accent/40 transition-all group"
    >
      <span
        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
          world.status === "generating"
            ? "bg-accent animate-pulse"
            : world.status === "running"
            ? "bg-green-500 animate-pulse"
            : world.status === "error"
            ? "bg-red-500"
            : "bg-hud-muted"
        }`}
      />

      <span className="font-mono text-[10px] text-hud-muted group-hover:text-hud-text truncate max-w-[180px]">
        {world.seed_prompt.slice(0, 40)}
      </span>

      <span className="font-mono text-[8px] text-accent uppercase tracking-wider flex-shrink-0">
        {statusLabel}
      </span>

      {world.status === "generating" && progress && (
        <div className="w-12 h-1 bg-hud-border rounded-full overflow-hidden flex-shrink-0">
          <div
            className="h-full bg-accent transition-all duration-500"
            style={{ width: `${progress.percent}%` }}
          />
        </div>
      )}
    </a>
  );
}

"use client";

import { motion } from "framer-motion";
import type { EpochItem } from "./types";

const THEME_COLORS: Record<NonNullable<EpochItem["dominantTheme"]>, string> = {
  prosperity: "#33ff88",
  conflict: "#ff4466",
  discovery: "#ffaa33",
  transition: "#a855f7",
};

interface EpochDividerProps {
  item: EpochItem;
}

export function EpochDivider({ item }: EpochDividerProps) {
  const color = item.dominantTheme
    ? THEME_COLORS[item.dominantTheme]
    : "#4f46e5";

  return (
    <div className="w-full py-4">
      <div className="flex items-center gap-3">
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="flex-1 h-[2px] origin-right"
          style={{
            background: `linear-gradient(90deg, transparent, ${color}60)`,
          }}
        />
        <span
          className="font-mono text-[11px] uppercase tracking-[0.25em] shrink-0"
          style={{ color }}
        >
          EPOCH {item.epoch}
        </span>
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="flex-1 h-[2px] origin-left"
          style={{
            background: `linear-gradient(90deg, ${color}60, transparent)`,
          }}
        />
      </div>
      {item.summary && (
        <p className="font-serif text-sm text-hud-muted text-center mt-1 italic">
          {item.summary}
        </p>
      )}
    </div>
  );
}

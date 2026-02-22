"use client";

import { motion } from "framer-motion";
import type { HeraldItem } from "./types";

interface HeraldBlockProps {
  item: HeraldItem;
}

export function HeraldBlock({ item }: HeraldBlockProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="w-full px-6 py-5 border border-herald/20 bg-herald/5 rounded-sm"
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-herald">
          ◆ HERALD
        </span>
        <span className="font-mono text-[11px] text-hud-label">
          E{item.epoch}.T{item.tick}
        </span>
      </div>
      <p className="font-serif text-xl leading-relaxed text-hud-text herald-glow">
        {item.text}
      </p>
    </motion.div>
  );
}

"use client";

import { useState, memo } from "react";
import { motion } from "framer-motion";
import { CornerMark } from "@/components/hud/CornerMark";
import type { WikiItem } from "./types";

interface WikiCrystalProps {
  item: WikiItem;
  onWikiClick?: (wikiId: string) => void;
  dimmed?: boolean;
}

export const WikiCrystal = memo(function WikiCrystal({ item, onWikiClick, dimmed }: WikiCrystalProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: dimmed ? 0.2 : 1, y: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="relative w-full px-4 py-3 border border-glow-blue/20 bg-glow-blue/5 rounded-sm cursor-pointer"
      onClick={() => {
        if (!expanded) onWikiClick?.(item.id);
        setExpanded(!expanded);
      }}
    >
      <CornerMark />

      <div className="flex items-center gap-2 mb-1">
        <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-glow-blue">
          ◇ KNOWLEDGE CRYSTALLIZED
        </span>
        <span className="font-mono text-[11px] text-hud-label">
          v{item.version}
        </span>
      </div>

      <h3 className="font-serif text-lg text-hud-text mb-1">
        {item.title}
      </h3>

      {expanded ? (
        <div className="font-serif text-sm text-hud-muted leading-relaxed mt-2 whitespace-pre-wrap">
          {item.content}
        </div>
      ) : (
        <p className="font-serif text-sm text-hud-muted leading-relaxed line-clamp-2">
          {item.content}
        </p>
      )}

      <div className="flex gap-3 mt-2 font-mono text-[10px] text-hud-label">
        {item.referencingAgents != null && (
          <span>{item.referencingAgents} agents reference</span>
        )}
        {item.disputes != null && item.disputes > 0 && (
          <span className="text-glow-red">{item.disputes} disputes</span>
        )}
      </div>
    </motion.div>
  );
});

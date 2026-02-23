"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import type { EventItem } from "./types";

const EVENT_ICONS: Record<EventItem["eventType"], string> = {
  crisis: "⚡",
  discovery: "📜",
  plague: "💀",
  leadership: "👑",
  general: "◈",
};

const EVENT_COLORS: Record<EventItem["eventType"], string> = {
  crisis: "text-glow-red",
  discovery: "text-glow-gold",
  plague: "text-hud-muted",
  leadership: "text-glow-blue",
  general: "text-accent",
};

interface EventBlockProps {
  item: EventItem;
  dimmed?: boolean;
}

export const EventBlock = memo(function EventBlock({ item, dimmed }: EventBlockProps) {
  const icon = EVENT_ICONS[item.eventType];
  const colorClass = EVENT_COLORS[item.eventType];

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: dimmed ? 0.2 : 1, y: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="w-full px-4 py-2"
    >
      <div className="event-line py-1">
        <span className={colorClass}>
          {icon} {item.description}
        </span>
      </div>
      {item.affectedAgents && item.affectedAgents.length > 0 && (
        <div className="font-mono text-[10px] text-hud-label mt-1 pl-4">
          Affects: {item.affectedAgents.join(", ")}
        </div>
      )}
    </motion.div>
  );
});

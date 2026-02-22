"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import type { ConversationItem } from "./types";

interface ConversationBlockProps {
  item: ConversationItem;
  onAgentClick?: (agentId: string) => void;
  dimmed?: boolean;
}

export function ConversationBlock({ item, onAgentClick, dimmed }: ConversationBlockProps) {
  const [expanded, setExpanded] = useState(false);
  const visibleMessages = expanded ? item.messages : item.messages.slice(0, 2);
  const hasMore = item.messages.length > 2;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: dimmed ? 0.2 : 1, y: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="w-full px-4 py-3 border border-hud-border/50 bg-void-light/50 rounded-sm"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-hud-label">
          E{item.epoch}.T{item.tick}
        </span>
        <span className="font-mono text-[11px] text-accent">
          {item.topic}
        </span>
        <span className="ml-auto font-mono text-[11px] text-hud-label">
          {item.participants.length} agents
        </span>
      </div>

      {/* Messages as script */}
      <div className="space-y-1.5">
        {visibleMessages.map((msg, i) => (
          <div
            key={i}
            className="flex items-start gap-2 pl-2"
            style={{ borderLeft: `2px solid ${msg.faction_color}30` }}
          >
            <button
              onClick={() => onAgentClick?.(msg.agent_id)}
              className="font-mono text-sm font-semibold shrink-0 hover:underline"
              style={{ color: msg.faction_color }}
            >
              <span style={{ color: msg.faction_color }}>●</span> {msg.agent_name}
            </button>
            <span className="font-sans text-sm text-hud-text leading-relaxed">
              {msg.content}
            </span>
          </div>
        ))}
      </div>

      {/* Expand toggle */}
      {hasMore && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 font-mono text-[11px] text-hud-muted hover:text-accent uppercase tracking-wider"
        >
          {expanded ? "▲ COLLAPSE" : `▼ ${item.messages.length - 2} MORE`}
        </button>
      )}

      {/* Participant chips */}
      <div className="flex gap-1.5 mt-2 flex-wrap">
        {item.participants.map((p) => (
          <button
            key={p.id}
            onClick={() => onAgentClick?.(p.id)}
            className="font-mono text-[10px] px-1.5 py-0.5 rounded-sm border border-hud-border/30 text-hud-muted hover:text-hud-text hover:border-hud-border transition-colors"
          >
            <span style={{ color: p.faction_color }}>●</span> {p.name}
          </button>
        ))}
      </div>
    </motion.div>
  );
}

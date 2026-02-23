"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import type { ConversationItem } from "./types";

interface ConversationBlockProps {
  item: ConversationItem;
  onAgentClick?: (agentId: string) => void;
  dimmed?: boolean;
}

/** Convert *text* to <em>text</em> while leaving the rest as-is */
function renderContent(raw: string) {
  const parts = raw.split(/(\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

export function ConversationBlock({ item, onAgentClick, dimmed }: ConversationBlockProps) {
  const [expanded, setExpanded] = useState(false);
  const visibleMessages = expanded ? item.messages : item.messages.slice(0, 3);
  const hasMore = item.messages.length > 3;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: dimmed ? 0.2 : 1, y: 0 }}
      transition={{ type: "spring", damping: 25, stiffness: 200 }}
      className="w-full px-4 py-3 border border-hud-border/50 bg-void-light/50 rounded-sm"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <span className="font-mono text-[11px] uppercase tracking-[0.15em] text-hud-label">
          E{item.epoch}.T{item.tick}
        </span>
        <span className="text-sm font-serif text-accent">
          {item.topic}
        </span>
        <span className="ml-auto font-mono text-[11px] text-hud-label">
          {item.participants.length} agents
        </span>
      </div>

      {/* Messages as chat bubbles */}
      <div className="space-y-4">
        {visibleMessages.map((msg, i) => (
          <div
            key={i}
            className="pl-3 py-2 pr-2 rounded-sm bg-void/50"
            style={{ borderLeft: `2px solid ${msg.faction_color}80` }}
          >
            <button
              onClick={() => onAgentClick?.(msg.agent_id)}
              className="font-mono text-xs font-semibold mb-1 block hover:underline"
              style={{ color: msg.faction_color }}
            >
              <span style={{ color: msg.faction_color }}>●</span> {msg.agent_name}
            </button>
            <p className="font-sans text-sm text-hud-text leading-relaxed whitespace-pre-wrap">
              {renderContent(msg.content)}
            </p>
          </div>
        ))}
      </div>

      {/* Expand toggle */}
      {hasMore && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 font-mono text-[11px] text-hud-muted hover:text-accent uppercase tracking-wider"
        >
          {expanded ? "▲ COLLAPSE" : `▼ ${item.messages.length - 3} MORE`}
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

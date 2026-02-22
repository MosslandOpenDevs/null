"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { AnimatePresence } from "framer-motion";
import { useSimulationStore } from "@/stores/simulation";
import { HeraldBlock } from "./HeraldBlock";
import { ConversationBlock } from "./ConversationBlock";
import { WikiCrystal } from "./WikiCrystal";
import { EventBlock } from "./EventBlock";
import { EpochDivider } from "./EpochDivider";
import type { ChronicleItem } from "./types";

interface ChronicleViewProps {
  className?: string;
  onAgentClick?: (agentId: string) => void;
  onWikiClick?: (wikiId: string) => void;
}

export function ChronicleView({ className, onAgentClick, onWikiClick }: ChronicleViewProps) {
  const { chronicleItems, focusFilter } = useSimulationStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);

  // Auto-scroll to top (newest items) when new content arrives
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [chronicleItems, autoScroll]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    setAutoScroll(el.scrollTop < 50);
  }, []);

  const isDimmed = (item: ChronicleItem): boolean => {
    if (!focusFilter || focusFilter.type === "all") return false;

    if (focusFilter.type === "agent") {
      if (item.type === "conversation") {
        return !item.participants.some((p) => p.id === focusFilter.id);
      }
      if (item.type === "event") {
        return !(item.affectedAgents?.includes(focusFilter.id ?? "") ?? false);
      }
      return false;
    }

    if (focusFilter.type === "faction") {
      if (item.type === "conversation") {
        return !item.participants.some((p) => p.faction_id === focusFilter.id);
      }
      return false;
    }

    return false;
  };

  const renderItem = (item: ChronicleItem) => {
    const dimmed = isDimmed(item);

    switch (item.type) {
      case "herald":
        return <HeraldBlock key={item.id} item={item} />;
      case "conversation":
        return (
          <ConversationBlock
            key={item.id}
            item={item}
            onAgentClick={onAgentClick}
            dimmed={dimmed}
          />
        );
      case "wiki":
        return (
          <WikiCrystal
            key={item.id}
            item={item}
            onWikiClick={onWikiClick}
            dimmed={dimmed}
          />
        );
      case "event":
        return <EventBlock key={item.id} item={item} dimmed={dimmed} />;
      case "epoch":
        return <EpochDivider key={item.id} item={item} />;
      default:
        return null;
    }
  };

  return (
    <div className={`flex flex-col flex-1 min-w-0 ${className || ""}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-hud-border">
        <span className="font-mono text-[13px] uppercase tracking-[0.2em] text-hud-label">
          LIVING CHRONICLE
        </span>
        {focusFilter && focusFilter.type !== "all" && (
          <span className="font-mono text-[11px] text-accent uppercase tracking-wider">
            FOCUS: {focusFilter.type} {focusFilter.id ? "active" : ""}
          </span>
        )}
        {!autoScroll && (
          <button
            onClick={() => {
              setAutoScroll(true);
              scrollRef.current?.scrollTo({ top: 0, behavior: "smooth" });
            }}
            className="font-mono text-[11px] text-accent hover:text-accent/80 uppercase tracking-wider"
          >
            ▲ LATEST
          </button>
        )}
      </div>

      {/* Chronicle Feed */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-3 space-y-3"
      >
        {chronicleItems.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <span className="font-mono text-base text-hud-muted animate-pulse-glow">
              AWAITING TRANSMISSION<span className="animate-blink">_</span>
            </span>
          </div>
        )}

        <AnimatePresence mode="popLayout">
          {chronicleItems.map(renderItem)}
        </AnimatePresence>
      </div>
    </div>
  );
}

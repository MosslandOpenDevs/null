"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useSimulationStore } from "@/stores/simulation";
import { CornerMark } from "./CornerMark";

function useCopyToast() {
  const [toast, setToast] = useState<string | null>(null);
  const copy = useCallback(async (text: string) => {
    await navigator.clipboard.writeText(text);
    setToast("Copied!");
    setTimeout(() => setToast(null), 1200);
  }, []);
  return { toast, copy };
}

interface FeedItem {
  id: string;
  type: "message" | "event" | "herald" | "epoch";
  epoch: number;
  timestamp: string;
  agentId?: string;
  agentName?: string;
  factionColor?: string;
  content: string;
}

export function LiveFeed() {
  const { events, agents, factions, selectedFaction, setSelectedAgent, setIntelTab } =
    useSimulationStore();
  const scrollRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [displayedItems, setDisplayedItems] = useState<FeedItem[]>([]);
  const { toast, copy } = useCopyToast();

  // Build agent/faction lookup
  const agentMap = new Map(agents.map((a) => [a.id, a]));
  const factionMap = new Map(factions.map((f) => [f.id, f]));

  // Derive faction color from agent
  const getFactionColor = useCallback((agentId: string): string => {
    const agent = agentMap.get(agentId);
    if (!agent?.faction_id) return "#6366f1";
    const faction = factionMap.get(agent.faction_id);
    return faction?.color || "#6366f1";
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agents, factions]);

  // Transform events to feed items
  useEffect(() => {
    const items: FeedItem[] = [];
    let lastEpoch = -1;

    for (const event of events) {
      // Epoch transition separator
      if (event.epoch !== lastEpoch && lastEpoch !== -1) {
        items.push({
          id: `epoch-${event.epoch}-${lastEpoch}`,
          type: "epoch",
          epoch: event.epoch,
          timestamp: event.timestamp,
          content: `EPOCH ${event.epoch}`,
        });
      }
      lastEpoch = event.epoch;

      if (event.type === "agent.message") {
        const agentId = event.payload.agent_id as string;
        const agent = agentMap.get(agentId);
        items.push({
          id: `msg-${event.timestamp}-${agentId}`,
          type: "message",
          epoch: event.epoch,
          timestamp: event.timestamp,
          agentId,
          agentName: agent?.name || (event.payload.agent_name as string) || "Unknown",
          factionColor: getFactionColor(agentId),
          content: event.payload.content as string,
        });
      } else if (event.type === "event.triggered") {
        items.push({
          id: `evt-${event.timestamp}`,
          type: "event",
          epoch: event.epoch,
          timestamp: event.timestamp,
          content: (event.payload.description as string) || (event.payload.text as string) || "Event occurred",
        });
      } else if (event.type === "herald.announcement") {
        items.push({
          id: `herald-${event.timestamp}`,
          type: "herald",
          epoch: event.epoch,
          timestamp: event.timestamp,
          content: event.payload.text as string,
        });
      } else if (event.type === "consensus.reached") {
        items.push({
          id: `consensus-${event.timestamp}`,
          type: "event",
          epoch: event.epoch,
          timestamp: event.timestamp,
          content: `CONSENSUS: ${event.payload.claim as string || "Agreement reached"}`,
        });
      }
    }

    // Filter by selected faction
    if (selectedFaction) {
      const factionAgentIds = new Set(
        agents.filter((a) => a.faction_id === selectedFaction).map((a) => a.id)
      );
      setDisplayedItems(
        items.filter(
          (item) =>
            item.type !== "message" || (item.agentId && factionAgentIds.has(item.agentId))
        )
      );
    } else {
      setDisplayedItems(items);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [events, selectedFaction, agents.length, factions.length]);

  // Auto-scroll
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [displayedItems, autoScroll]);

  // Detect manual scroll
  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
    setAutoScroll(isAtBottom);
  }, []);

  return (
    <div className="relative flex flex-col flex-1 bg-void border-x border-hud-border min-w-0">
      <CornerMark />
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-hud-border">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-hud-label">
          LIVE FEED
        </span>
        {!autoScroll && (
          <button
            onClick={() => {
              setAutoScroll(true);
              scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
            }}
            className="font-mono text-[9px] text-accent hover:text-accent/80 uppercase tracking-wider"
          >
            ▼ LATEST
          </button>
        )}
      </div>

      {/* Feed */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-3 space-y-1"
      >
        {displayedItems.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <span className="font-mono text-[11px] text-hud-muted animate-pulse-glow">
              AWAITING TRANSMISSION<span className="animate-blink">_</span>
            </span>
          </div>
        )}

        {displayedItems.map((item) => {
          if (item.type === "epoch") {
            return (
              <div key={item.id} className="epoch-line py-2 my-1">
                {item.content}
              </div>
            );
          }

          if (item.type === "event") {
            return (
              <div key={item.id} className="event-line py-1 my-1">
                {item.content}
              </div>
            );
          }

          if (item.type === "herald") {
            return (
              <div
                key={item.id}
                className="my-2 p-2 border border-herald/20 bg-herald/5 font-mono text-[11px]"
              >
                <div className="text-herald text-[9px] uppercase tracking-[0.15em] mb-1">
                  ◆ HERALD
                </div>
                <div className="text-hud-text italic">{item.content}</div>
              </div>
            );
          }

          // Message
          return (
            <div key={item.id} className="animate-fade-in font-mono text-[11px] leading-relaxed group">
              <button
                onClick={() => {
                  if (item.agentId) {
                    setSelectedAgent(item.agentId);
                    setIntelTab("agent");
                  }
                }}
                className="hover:underline font-semibold"
                style={{ color: item.factionColor }}
              >
                {item.agentName}
              </button>
              <span className="text-hud-muted mx-1">:</span>
              <span className="text-hud-text">{item.content}</span>
              <button
                onClick={() => copy(`${item.agentName}: ${item.content}`)}
                className="ml-1 opacity-0 group-hover:opacity-100 text-[8px] text-hud-muted hover:text-accent transition-opacity"
                title="Copy message"
              >
                📋
              </button>
            </div>
          );
        })}
      </div>

      {/* Copy toast */}
      {toast && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1 bg-accent text-void font-mono text-[9px] uppercase tracking-wider">
          {toast}
        </div>
      )}
    </div>
  );
}

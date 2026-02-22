"use client";

import { useEffect, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { useSimulationStore } from "@/stores/simulation";
import { useWSClient } from "@/lib/wsClient";
import { StatusBar } from "@/components/hud/StatusBar";
import { ChronicleView } from "@/components/chronicle/ChronicleView";
import { MinimapSidebar } from "@/components/minimap/MinimapSidebar";
import { TimelineRibbon } from "@/components/TimelineRibbon";
import { CommandPalette } from "@/components/CommandPalette";
import { OraclePanel } from "@/components/OraclePanel";
import { HeraldToast } from "@/components/HeraldToast";
import { Scanline } from "@/components/hud/Scanline";
import { InterventionBar } from "@/components/divine/InterventionBar";

const GENERATING_MESSAGES = [
  "Forging the fabric of reality...",
  "Summoning factions from the void...",
  "Weaving agent personas...",
  "Establishing power dynamics...",
  "Constructing knowledge networks...",
  "Seeding initial conflicts...",
];

export default function WorldPage() {
  const { id, locale } = useParams<{ id: string; locale: string }>();
  const { connect, disconnect } = useWSClient();
  const {
    fetchWorld,
    world,
    activeAgentIds,
    openOracle,
    setFocusFilter,
    focusFilter,
  } = useSimulationStore();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (id) {
      fetchWorld(id);
      connect(id);
      return () => disconnect();
    }
  }, [id, connect, disconnect, fetchWorld]);

  // Poll while world is generating
  useEffect(() => {
    if (world?.status === "generating" && id) {
      pollRef.current = setInterval(() => {
        fetchWorld(id);
      }, 2000);
      return () => {
        if (pollRef.current) clearInterval(pollRef.current);
      };
    }
    if (pollRef.current && world?.status !== "generating") {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, [world?.status, id, fetchWorld]);

  const handleAgentClick = useCallback(
    (agentId: string) => {
      openOracle({ type: "agent", id: agentId });
    },
    [openOracle]
  );

  const handleWikiClick = useCallback(
    (wikiId: string) => {
      openOracle({ type: "wiki", id: wikiId });
    },
    [openOracle]
  );

  const handleFactionClick = useCallback(
    (factionId: string) => {
      // Toggle faction focus
      if (focusFilter.type === "faction" && focusFilter.id === factionId) {
        setFocusFilter({ type: "all" });
      } else {
        setFocusFilter({ type: "faction", id: factionId });
      }
    },
    [focusFilter, setFocusFilter]
  );

  const handleMinimapAgentClick = useCallback(
    (agentId: string) => {
      // Toggle agent focus
      if (focusFilter.type === "agent" && focusFilter.id === agentId) {
        setFocusFilter({ type: "all" });
      } else {
        setFocusFilter({ type: "agent", id: agentId });
      }
      openOracle({ type: "agent", id: agentId });
    },
    [focusFilter, setFocusFilter, openOracle]
  );

  if (!world) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-void">
        <div className="font-mono text-base text-hud-muted animate-pulse-glow">
          INITIALIZING<span className="animate-blink">_</span>
        </div>
      </div>
    );
  }

  if (world.status === "generating") {
    const progress = (world.config as Record<string, unknown>)?._genesis_progress as
      | { step: string; step_num: number; total_steps: number; detail: string; percent: number }
      | undefined;
    const percent = progress?.percent ?? 0;
    const detail = progress?.detail || GENERATING_MESSAGES[Math.floor(Date.now() / 3000) % GENERATING_MESSAGES.length];
    const stepLabel = progress ? `${progress.step_num} / ${progress.total_steps}` : "";

    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-void gap-6">
        <div className="relative">
          <div className="w-16 h-16 border border-accent/30 rotate-45 animate-spin" style={{ animationDuration: "3s" }} />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-3 h-3 bg-accent rounded-full animate-pulse" />
          </div>
        </div>
        <div className="text-center space-y-3 w-full max-w-sm">
          <div className="font-mono text-base text-accent animate-pulse">
            GENESIS IN PROGRESS
          </div>
          <div className="w-full h-1.5 bg-hud-border rounded-full overflow-hidden">
            <div
              className="h-full bg-accent transition-all duration-700 ease-out"
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="flex justify-between items-center">
            <span className="font-mono text-sm text-hud-muted">{detail}</span>
            <span className="font-mono text-sm text-accent">{percent}%</span>
          </div>
          {stepLabel && (
            <div className="font-mono text-sm text-hud-label">
              STEP {stepLabel}
            </div>
          )}
          <div className="font-mono text-sm text-hud-label mt-2">
            {world.seed_prompt.slice(0, 80)}{world.seed_prompt.length > 80 ? "..." : ""}
          </div>
        </div>
      </div>
    );
  }

  if (world.status === "error") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-void gap-4">
        <div className="font-mono text-base text-danger">
          GENESIS FAILED
        </div>
        <div className="font-mono text-sm text-hud-muted">
          World creation encountered an error.
        </div>
        <a href={`/${locale}`} className="font-mono text-sm text-accent hover:text-accent/80">
          &larr; BACK TO OBSERVATORY
        </a>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col w-screen h-screen overflow-hidden bg-void">
      <Scanline />
      <HeraldToast />

      {/* Status bar */}
      <StatusBar />

      {/* Divine Intervention bar */}
      <InterventionBar />

      {/* Main content: Chronicle (left) + Minimap (right) */}
      <div className="flex flex-1 min-h-0">
        <ChronicleView
          className="flex-1"
          onAgentClick={handleAgentClick}
          onWikiClick={handleWikiClick}
        />
        <MinimapSidebar
          className="w-64 hidden lg:flex"
          activeAgentIds={activeAgentIds}
          onAgentClick={handleMinimapAgentClick}
          onFactionClick={handleFactionClick}
        />
      </div>

      {/* Timeline */}
      <TimelineRibbon />

      {/* Overlays */}
      <CommandPalette />
      <OraclePanel />
    </div>
  );
}

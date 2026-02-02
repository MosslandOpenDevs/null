"use client";

import { useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import { useSimulationStore } from "@/stores/simulation";
import { useWSClient } from "@/lib/wsClient";
import { StatusBar } from "@/components/hud/StatusBar";
import { KnowledgeHub } from "@/components/KnowledgeHub";
import { SystemPulse } from "@/components/SystemPulse";
import { TimelineRibbon } from "@/components/TimelineRibbon";
import { CommandPalette } from "@/components/CommandPalette";
import { BreadcrumbBar } from "@/components/BreadcrumbBar";
import { BookmarkDrawer } from "@/components/BookmarkDrawer";
import { Scanline } from "@/components/hud/Scanline";
import { useBookmarkStore } from "@/stores/bookmarks";

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
  const { fetchWorld, world } = useSimulationStore();
  const { setDrawerOpen } = useBookmarkStore();
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
    // Stop polling once no longer generating
    if (pollRef.current && world?.status !== "generating") {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, [world?.status, id, fetchWorld]);

  if (!world) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-void">
        <div className="font-mono text-[11px] text-hud-muted animate-pulse-glow">
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
          <div className="font-mono text-[11px] text-accent animate-pulse">
            GENESIS IN PROGRESS
          </div>
          {/* Progress bar */}
          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-accent transition-all duration-700 ease-out"
              style={{ width: `${percent}%` }}
            />
          </div>
          <div className="flex justify-between items-center">
            <span className="font-mono text-[10px] text-hud-muted">{detail}</span>
            <span className="font-mono text-[10px] text-accent">{percent}%</span>
          </div>
          {stepLabel && (
            <div className="font-mono text-[9px] text-hud-label">
              STEP {stepLabel}
            </div>
          )}
          <div className="font-mono text-[9px] text-hud-label mt-2">
            {world.seed_prompt.slice(0, 80)}{world.seed_prompt.length > 80 ? "..." : ""}
          </div>
        </div>
      </div>
    );
  }

  if (world.status === "error") {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-void gap-4">
        <div className="font-mono text-[11px] text-danger">
          GENESIS FAILED
        </div>
        <div className="font-mono text-[9px] text-hud-muted">
          World creation encountered an error.
        </div>
        <a href={`/${locale}`} className="font-mono text-[10px] text-accent hover:text-accent/80">
          &larr; BACK TO OBSERVATORY
        </a>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col w-screen h-screen overflow-hidden bg-void">
      <Scanline />

      {/* Breadcrumb */}
      <BreadcrumbBar
        items={[
          { label: "Observatory", href: `/${locale}` },
          { label: world.seed_prompt.slice(0, 40) + (world.seed_prompt.length > 40 ? "..." : "") },
        ]}
      />

      {/* Status bar */}
      <StatusBar />

      {/* Main content: 2-column layout — KnowledgeHub (left ~70%) + SystemPulse (right ~30%) */}
      <div className="flex flex-1 min-h-0">
        <div className="flex-1 min-w-0">
          <KnowledgeHub />
        </div>
        <SystemPulse />
      </div>

      {/* Timeline */}
      <TimelineRibbon />

      {/* Overlays */}
      <CommandPalette />
      <BookmarkDrawer />

      {/* Bookmark toggle */}
      <button
        onClick={() => setDrawerOpen(true)}
        className="fixed right-4 bottom-4 z-40 px-3 py-2 bg-void-light border border-hud-border hover:border-accent font-mono text-[9px] text-hud-muted hover:text-accent uppercase tracking-wider transition-colors"
      >
        BOOKMARKS
      </button>
    </div>
  );
}

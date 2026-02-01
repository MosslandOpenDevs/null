"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { useSimulationStore } from "@/stores/simulation";
import { useWSClient } from "@/lib/wsClient";
import { StatusBar } from "@/components/hud/StatusBar";
import { FactionSidebar } from "@/components/hud/FactionSidebar";
import { LiveFeed } from "@/components/hud/LiveFeed";
import { IntelPanel } from "@/components/hud/IntelPanel";
import { TimelineRibbon } from "@/components/TimelineRibbon";
import { CommandPalette } from "@/components/CommandPalette";
import { Scanline } from "@/components/hud/Scanline";

export default function WorldPage() {
  const { id } = useParams<{ id: string }>();
  const { connect, disconnect } = useWSClient();
  const { fetchWorld, world } = useSimulationStore();

  useEffect(() => {
    if (id) {
      fetchWorld(id);
      connect(id);
      return () => disconnect();
    }
  }, [id, connect, disconnect, fetchWorld]);

  if (!world) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-void">
        <div className="font-mono text-[11px] text-hud-muted animate-pulse-glow">
          INITIALIZING<span className="animate-blink">_</span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col w-screen h-screen overflow-hidden bg-void">
      <Scanline />

      {/* Status bar */}
      <StatusBar />

      {/* Main content: 3-column layout */}
      <div className="flex flex-1 min-h-0">
        <FactionSidebar />
        <LiveFeed />
        <IntelPanel />
      </div>

      {/* Timeline */}
      <TimelineRibbon />

      {/* Overlays */}
      <CommandPalette />
    </div>
  );
}

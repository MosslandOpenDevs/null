"use client";

import { useState } from "react";
import { useSimulationStore } from "@/stores/simulation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

const EVENT_TYPES = [
  { icon: "⚡", label: "CRISIS", type: "crisis", description: "A sudden crisis shakes the world" },
  { icon: "📜", label: "DISCOVERY", type: "discovery", description: "A groundbreaking discovery is made" },
  { icon: "💀", label: "PLAGUE", type: "plague", description: "A mysterious plague spreads through the region" },
  { icon: "👑", label: "LEADERSHIP", type: "leadership", description: "A leadership challenge erupts" },
] as const;

export function InterventionBar() {
  const { world, agents } = useSimulationStore();
  const [showWhisper, setShowWhisper] = useState(false);
  const [showTopicInput, setShowTopicInput] = useState(false);
  const [whisperTarget, setWhisperTarget] = useState("");
  const [whisperText, setWhisperText] = useState("");
  const [topicText, setTopicText] = useState("");

  if (!world || world.status !== "running") return null;

  const triggerEvent = async (eventType: string, description: string) => {
    try {
      await fetch(`${API_URL}/api/worlds/${world.id}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: eventType, description }),
      });
    } catch {
      // Event endpoint may not exist yet
    }
  };

  const sendWhisper = async () => {
    if (!whisperTarget || !whisperText.trim()) return;
    try {
      await fetch(`${API_URL}/api/worlds/${world.id}/agents/${whisperTarget}/whisper`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: whisperText }),
      });
      setWhisperText("");
      setShowWhisper(false);
    } catch {
      // Whisper endpoint may not exist yet
    }
  };

  const sendSeedBomb = async () => {
    if (!topicText.trim()) return;
    try {
      await fetch(`${API_URL}/api/worlds/${world.id}/seed-bomb`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: topicText }),
      });
      setTopicText("");
      setShowTopicInput(false);
    } catch {
      // Seed-bomb endpoint may not exist yet
    }
  };

  return (
    <div className="px-4 py-1.5 border-b border-hud-border bg-void-light/50">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-hud-label mr-2">
          DIVINE INTERVENTION
        </span>

        {/* Event inject buttons */}
        {EVENT_TYPES.map((evt) => (
          <button
            key={evt.type}
            onClick={() => triggerEvent(evt.type, evt.description)}
            className="font-mono text-[10px] px-2 py-1 border border-hud-border/50 text-hud-muted hover:text-hud-text hover:border-hud-border transition-colors uppercase tracking-wider"
            title={`Inject ${evt.label} event`}
          >
            {evt.icon} {evt.label}
          </button>
        ))}

        <div className="w-px h-4 bg-hud-border/50 mx-1" />

        {/* Whisper button */}
        <button
          onClick={() => setShowWhisper(!showWhisper)}
          className="font-mono text-[10px] px-2 py-1 border border-hud-border/50 text-hud-muted hover:text-accent hover:border-accent/30 transition-colors uppercase tracking-wider"
        >
          🔮 WHISPER
        </button>

        {/* Topic injection button */}
        <button
          onClick={() => setShowTopicInput(!showTopicInput)}
          className="font-mono text-[10px] px-2 py-1 border border-hud-border/50 text-hud-muted hover:text-glow-gold hover:border-glow-gold/30 transition-colors uppercase tracking-wider"
        >
          💣 SEED BOMB
        </button>
      </div>

      {/* Whisper input */}
      {showWhisper && (
        <div className="flex items-center gap-2 mt-2">
          <select
            value={whisperTarget}
            onChange={(e) => setWhisperTarget(e.target.value)}
            className="bg-void border border-hud-border font-mono text-[11px] text-hud-text px-2 py-1 focus:outline-none focus:border-accent"
          >
            <option value="">Select agent...</option>
            {agents.map((a) => (
              <option key={a.id} value={a.id}>{a.name}</option>
            ))}
          </select>
          <input
            value={whisperText}
            onChange={(e) => setWhisperText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendWhisper()}
            placeholder="Whisper to agent..."
            className="flex-1 bg-void border border-hud-border font-mono text-[11px] text-hud-text px-2 py-1 placeholder-hud-label focus:outline-none focus:border-accent"
          />
          <button
            onClick={sendWhisper}
            className="font-mono text-[10px] px-2 py-1 bg-accent/10 border border-accent/30 text-accent hover:bg-accent/20 transition-colors uppercase"
          >
            SEND
          </button>
        </div>
      )}

      {/* Topic input */}
      {showTopicInput && (
        <div className="flex items-center gap-2 mt-2">
          <input
            value={topicText}
            onChange={(e) => setTopicText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendSeedBomb()}
            placeholder="Enter topic to inject..."
            className="flex-1 bg-void border border-hud-border font-mono text-[11px] text-hud-text px-2 py-1 placeholder-hud-label focus:outline-none focus:border-glow-gold/50"
          />
          <button
            onClick={sendSeedBomb}
            className="font-mono text-[10px] px-2 py-1 bg-glow-gold/10 border border-glow-gold/30 text-glow-gold hover:bg-glow-gold/20 transition-colors uppercase"
          >
            DETONATE
          </button>
        </div>
      )}
    </div>
  );
}

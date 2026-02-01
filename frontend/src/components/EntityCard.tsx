"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

interface EntityMention {
  id: string;
  source_type: string;
  source_id: string;
  mention_text: string;
  confidence: number;
}

interface SemanticNeighbor {
  id: string;
  entity_a_type: string;
  entity_a_id: string;
  entity_b_type: string;
  entity_b_id: string;
  similarity: number;
}

interface EntityCardProps {
  worldId: string;
  entityType: string;
  entityId: string;
  entityName: string;
  onClose: () => void;
  position?: { x: number; y: number };
}

export function EntityCard({
  worldId,
  entityType,
  entityId,
  entityName,
  onClose,
  position,
}: EntityCardProps) {
  const [mentions, setMentions] = useState<EntityMention[]>([]);
  const [neighbors, setNeighbors] = useState<SemanticNeighbor[]>([]);
  const [tab, setTab] = useState<"mentions" | "neighbors">("mentions");

  useEffect(() => {
    fetch(`${API_URL}/api/worlds/${worldId}/entities/${entityType}/${entityId}/mentions`)
      .then((r) => r.json())
      .then(setMentions)
      .catch(() => {});

    fetch(`${API_URL}/api/worlds/${worldId}/entities/${entityType}/${entityId}/neighbors`)
      .then((r) => r.json())
      .then(setNeighbors)
      .catch(() => {});
  }, [worldId, entityType, entityId]);

  const style = position
    ? { position: "fixed" as const, left: position.x, top: position.y, zIndex: 60 }
    : { position: "relative" as const };

  return (
    <div
      style={style}
      className="w-72 bg-void-light border border-hud-border shadow-lg"
    >
      <div className="corner-mark corner-mark-tl" />
      <div className="corner-mark corner-mark-tr" />

      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-hud-border">
        <div>
          <div className="font-mono text-[11px] text-hud-text font-semibold truncate">
            {entityName}
          </div>
          <div className="font-mono text-[8px] text-hud-label uppercase">
            {entityType.replace("_", " ")}
          </div>
        </div>
        <button
          onClick={onClose}
          className="font-mono text-[10px] text-hud-muted hover:text-danger"
        >
          ✕
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-hud-border">
        <button
          onClick={() => setTab("mentions")}
          className={`flex-1 py-1 font-mono text-[9px] uppercase tracking-wider ${
            tab === "mentions" ? "text-accent border-b border-accent" : "text-hud-muted"
          }`}
        >
          Mentions ({mentions.length})
        </button>
        <button
          onClick={() => setTab("neighbors")}
          className={`flex-1 py-1 font-mono text-[9px] uppercase tracking-wider ${
            tab === "neighbors" ? "text-accent border-b border-accent" : "text-hud-muted"
          }`}
        >
          Neighbors ({neighbors.length})
        </button>
      </div>

      {/* Content */}
      <div className="max-h-48 overflow-y-auto p-2 space-y-1">
        {tab === "mentions" &&
          (mentions.length === 0 ? (
            <div className="font-mono text-[9px] text-hud-label text-center py-2">
              No mentions found
            </div>
          ) : (
            mentions.map((m) => (
              <div
                key={m.id}
                className="px-2 py-1 border border-hud-border text-left"
              >
                <div className="font-mono text-[9px] text-hud-text">
                  &quot;{m.mention_text}&quot;
                </div>
                <div className="font-mono text-[8px] text-hud-label">
                  {m.source_type} · {(m.confidence * 100).toFixed(0)}%
                </div>
              </div>
            ))
          ))}

        {tab === "neighbors" &&
          (neighbors.length === 0 ? (
            <div className="font-mono text-[9px] text-hud-label text-center py-2">
              No neighbors found
            </div>
          ) : (
            neighbors.map((n) => (
              <div
                key={n.id}
                className="px-2 py-1 border border-hud-border text-left"
              >
                <div className="font-mono text-[9px] text-hud-text">
                  {n.entity_b_type.replace("_", " ")}
                </div>
                <div className="font-mono text-[8px] text-hud-label">
                  similarity: {(n.similarity * 100).toFixed(0)}%
                </div>
              </div>
            ))
          ))}
      </div>
    </div>
  );
}

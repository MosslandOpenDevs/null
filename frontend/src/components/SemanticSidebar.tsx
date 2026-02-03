"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

interface NeighborInfo {
  id: string;
  entity_a_type: string;
  entity_a_id: string;
  entity_b_type: string;
  entity_b_id: string;
  similarity: number;
}

interface SemanticSidebarProps {
  worldId: string;
  entityType: string;
  entityId: string;
}

export function SemanticSidebar({
  worldId,
  entityType,
  entityId,
}: SemanticSidebarProps) {
  const [neighbors, setNeighbors] = useState<NeighborInfo[]>([]);

  useEffect(() => {
    if (!entityId) return;
    fetch(
      `${API_URL}/api/worlds/${worldId}/entities/${entityType}/${entityId}/neighbors`
    )
      .then((r) => r.json())
      .then(setNeighbors)
      .catch(() => {});
  }, [worldId, entityType, entityId]);

  if (neighbors.length === 0) return null;

  return (
    <div className="border-t border-hud-border mt-2 pt-2">
      <div className="font-mono text-sm text-hud-label uppercase tracking-wider mb-1">
        SEMANTIC NEIGHBORS
      </div>
      <div className="space-y-0.5">
        {neighbors.slice(0, 5).map((n) => (
          <div
            key={n.id}
            className="flex items-center justify-between px-1 py-0.5"
          >
            <span className="font-mono text-sm text-hud-muted truncate flex-1">
              {n.entity_b_type.replace("_", " ")}
            </span>
            <span className="font-mono text-[11px] text-accent flex-shrink-0 ml-1">
              {(n.similarity * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

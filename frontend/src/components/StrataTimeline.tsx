"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

interface Stratum {
  id: string;
  world_id: string;
  epoch: number;
  summary: string;
  emerged_concepts: string[];
  faded_concepts: string[];
  dominant_themes: string[];
}

interface StrataTimelineProps {
  worldId: string;
}

export function StrataTimeline({ worldId }: StrataTimelineProps) {
  const [strata, setStrata] = useState<Stratum[]>([]);
  const [selected, setSelected] = useState<Stratum | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/api/worlds/${worldId}/strata`)
      .then((r) => r.json())
      .then(setStrata)
      .catch(() => {});
  }, [worldId]);

  if (strata.length === 0) {
    return (
      <div className="font-mono text-[10px] text-hud-label text-center py-4">
        NO STRATA DATA YET
      </div>
    );
  }

  if (selected) {
    return (
      <div className="p-3 space-y-3">
        <button
          onClick={() => setSelected(null)}
          className="font-mono text-[9px] text-accent hover:text-accent/80 uppercase tracking-wider"
        >
          ← BACK TO TIMELINE
        </button>

        <div>
          <h3 className="font-mono text-sm text-hud-text font-semibold">
            EPOCH {selected.epoch}
          </h3>
          <p className="font-mono text-[10px] text-hud-muted mt-1 leading-relaxed">
            {selected.summary}
          </p>
        </div>

        {selected.emerged_concepts.length > 0 && (
          <div>
            <div className="font-mono text-[9px] text-success uppercase tracking-wider mb-1">
              ▲ EMERGED
            </div>
            <div className="flex flex-wrap gap-1">
              {selected.emerged_concepts.map((c, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 text-[8px] font-mono text-success border border-success/30 rounded"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {selected.faded_concepts.length > 0 && (
          <div>
            <div className="font-mono text-[9px] text-danger uppercase tracking-wider mb-1">
              ▼ FADED
            </div>
            <div className="flex flex-wrap gap-1">
              {selected.faded_concepts.map((c, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 text-[8px] font-mono text-danger border border-danger/30 rounded"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {selected.dominant_themes.length > 0 && (
          <div>
            <div className="font-mono text-[9px] text-herald uppercase tracking-wider mb-1">
              ◆ DOMINANT THEMES
            </div>
            <div className="flex flex-wrap gap-1">
              {selected.dominant_themes.map((t, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 text-[8px] font-mono text-herald border border-herald/30 rounded"
                >
                  {t}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="p-3 space-y-1">
      <div className="font-mono text-[9px] text-hud-label uppercase tracking-wider mb-2">
        TEMPORAL STRATA
      </div>
      {strata.map((s) => (
        <button
          key={s.id}
          onClick={() => setSelected(s)}
          className="w-full text-left p-2 border border-hud-border hover:border-hud-border-active transition-colors"
        >
          <div className="flex items-center justify-between">
            <span className="font-mono text-[10px] text-hud-text">
              EPOCH {s.epoch}
            </span>
            <span className="font-mono text-[8px] text-hud-label">
              {s.dominant_themes.length} themes
            </span>
          </div>
          <div className="font-mono text-[9px] text-hud-muted mt-0.5 truncate">
            {s.summary}
          </div>
          <div className="flex gap-1 mt-1">
            {s.emerged_concepts.slice(0, 3).map((c, i) => (
              <span
                key={i}
                className="px-1 py-0.5 text-[7px] font-mono text-success/60 border border-success/20 rounded"
              >
                +{c}
              </span>
            ))}
          </div>
        </button>
      ))}
    </div>
  );
}

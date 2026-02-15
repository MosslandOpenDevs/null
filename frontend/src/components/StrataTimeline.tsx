"use client";

import { useState, useEffect } from "react";
import { useLocale } from "next-intl";
import { useStrataStore, type StratumData } from "@/stores/strata";

interface StrataTimelineProps {
  worldId: string;
}

export function StrataTimeline({ worldId }: StrataTimelineProps) {
  const locale = useLocale();
  const ts = (en: string, ko?: string | null) => (locale === "ko" && ko) ? ko : en;
  const { strata, comparison, comparisonLoading, fetchStrata, fetchComparison, clearComparison } =
    useStrataStore();
  const [selected, setSelected] = useState<StratumData | null>(null);
  const selectedEpoch = selected?.epoch ?? null;

  useEffect(() => {
    fetchStrata(worldId);
    setSelected(null);
    clearComparison();
  }, [worldId, fetchStrata, clearComparison]);

  useEffect(() => {
    if (selectedEpoch === null) {
      clearComparison();
      return;
    }
    if (selectedEpoch <= 0) {
      clearComparison();
      return;
    }

    fetchComparison(worldId, selectedEpoch - 1, selectedEpoch);
  }, [worldId, selectedEpoch, fetchComparison, clearComparison]);

  if (strata.length === 0) {
    return (
      <div className="font-mono text-sm text-hud-label text-center py-4">
        NO STRATA DATA YET
      </div>
    );
  }

  if (selected) {
    return (
      <div className="p-3 space-y-3">
        <button
          onClick={() => setSelected(null)}
          className="font-mono text-base text-accent hover:text-accent/80 uppercase tracking-wider"
        >
          ← BACK TO TIMELINE
        </button>

        <div>
          <h3 className="font-mono text-base text-hud-text font-semibold">
            EPOCH {selected.epoch}
          </h3>
          <p className="font-sans text-base text-hud-muted mt-1 leading-relaxed">
            {ts(selected.summary, selected.summary_ko)}
          </p>
        </div>

        {(comparisonLoading || comparison) && (
          <div className="border border-hud-border rounded p-2 space-y-2">
            <div className="font-mono text-sm text-hud-label uppercase tracking-wider">
              EPOCH SHIFT
              {comparison && (
                <span className="ml-2 text-hud-muted normal-case">
                  E{comparison.from_epoch} → E{comparison.to_epoch}
                </span>
              )}
            </div>
            {comparisonLoading && (
              <div className="font-mono text-sm text-hud-muted">Comparing strata...</div>
            )}
            {comparison && (
              <div className="space-y-1">
                {comparison.added_themes.length > 0 && (
                  <div className="font-mono text-sm text-success">
                    + Themes: {comparison.added_themes.join(", ")}
                  </div>
                )}
                {comparison.removed_themes.length > 0 && (
                  <div className="font-mono text-sm text-danger">
                    - Themes: {comparison.removed_themes.join(", ")}
                  </div>
                )}
                {comparison.persisted_themes.length > 0 && (
                  <div className="font-mono text-sm text-hud-muted">
                    = Stable: {comparison.persisted_themes.join(", ")}
                  </div>
                )}
                {comparison.newly_emerged_concepts.length > 0 && (
                  <div className="font-mono text-sm text-success">
                    + Emerged: {comparison.newly_emerged_concepts.join(", ")}
                  </div>
                )}
                {comparison.newly_faded_concepts.length > 0 && (
                  <div className="font-mono text-sm text-danger">
                    - Faded: {comparison.newly_faded_concepts.join(", ")}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {selected.emerged_concepts.length > 0 && (
          <div>
            <div className="font-mono text-base text-success uppercase tracking-wider mb-1">
              ▲ EMERGED
            </div>
            <div className="flex flex-wrap gap-1">
              {selected.emerged_concepts.map((c, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 text-[13px] font-mono text-success border border-success/30 rounded"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {selected.faded_concepts.length > 0 && (
          <div>
            <div className="font-mono text-base text-danger uppercase tracking-wider mb-1">
              ▼ FADED
            </div>
            <div className="flex flex-wrap gap-1">
              {selected.faded_concepts.map((c, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 text-[13px] font-mono text-danger border border-danger/30 rounded"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {selected.dominant_themes.length > 0 && (
          <div>
            <div className="font-mono text-base text-herald uppercase tracking-wider mb-1">
              ◆ DOMINANT THEMES
            </div>
            <div className="flex flex-wrap gap-1">
              {selected.dominant_themes.map((t, i) => (
                <span
                  key={i}
                  className="px-1.5 py-0.5 text-[13px] font-mono text-herald border border-herald/30 rounded"
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
      <div className="font-mono text-base text-hud-label uppercase tracking-wider mb-2">
        TEMPORAL STRATA
      </div>
      {strata.map((s) => (
        <button
          key={s.id}
          onClick={() => setSelected(s)}
          className="w-full text-left p-2 border border-hud-border hover:border-hud-border-active transition-colors"
        >
          <div className="flex items-center justify-between">
            <span className="font-mono text-sm text-hud-text">
              EPOCH {s.epoch}
            </span>
            <span className="font-mono text-[13px] text-hud-label">
              {s.dominant_themes.length} themes
            </span>
          </div>
          <div className="font-sans text-sm text-hud-muted mt-0.5 truncate">
            {ts(s.summary, s.summary_ko)}
          </div>
          <div className="flex gap-1 mt-1">
            {s.emerged_concepts.slice(0, 3).map((c, i) => (
              <span
                key={i}
                className="px-1.5 py-0.5 text-[13px] font-mono text-success/60 border border-success/20 rounded"
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

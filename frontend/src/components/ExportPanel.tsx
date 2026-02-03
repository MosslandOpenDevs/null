"use client";

import { useState } from "react";
import { useSimulationStore } from "@/stores/simulation";

const EXPORT_TYPES = [
  { id: "wiki", label: "Wiki Pages", formats: ["md", "json"] },
  { id: "conversations", label: "Conversations", formats: ["jsonl", "json"] },
  { id: "knowledge-graph", label: "Knowledge Graph", formats: ["csv", "json"] },
  { id: "agents", label: "Agents", formats: ["json"] },
  { id: "all", label: "Everything", formats: ["jsonl"] },
  { id: "training", label: "Training Data", formats: ["chatml", "alpaca", "sharegpt"] },
];

interface ExportPanelProps {
  open: boolean;
  onClose: () => void;
}

export function ExportPanel({ open, onClose }: ExportPanelProps) {
  const { world, exportWorld } = useSimulationStore();
  const [selectedType, setSelectedType] = useState("wiki");
  const [selectedFormat, setSelectedFormat] = useState("md");
  const [exporting, setExporting] = useState(false);

  if (!open || !world) return null;

  const currentType = EXPORT_TYPES.find((t) => t.id === selectedType)!;

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportWorld(world.id, selectedType, selectedFormat);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />
      <div className="relative w-full max-w-md bg-void-light border border-hud-border p-6 space-y-4">
        <div className="corner-mark corner-mark-tl" />
        <div className="corner-mark corner-mark-tr" />
        <div className="corner-mark corner-mark-bl" />
        <div className="corner-mark corner-mark-br" />

        <h2 className="font-mono text-base text-hud-text uppercase tracking-[0.15em]">
          EXPORT DATA
        </h2>

        <div className="font-mono text-[13px] text-hud-muted">
          World: {(world.config as Record<string, unknown>)?.description
            ? String((world.config as Record<string, unknown>).description).slice(0, 50)
            : world.seed_prompt.slice(0, 50)}
        </div>

        {/* Type selection */}
        <div>
          <div className="font-mono text-sm uppercase tracking-[0.15em] text-hud-label mb-2">
            DATA TYPE
          </div>
          <div className="grid grid-cols-2 gap-1">
            {EXPORT_TYPES.map((type) => (
              <button
                key={type.id}
                onClick={() => {
                  setSelectedType(type.id);
                  setSelectedFormat(type.formats[0]);
                }}
                className={`font-mono text-[13px] px-2 py-1.5 border transition-colors ${
                  selectedType === type.id
                    ? "border-accent text-accent"
                    : "border-hud-border text-hud-muted hover:text-hud-text"
                }`}
              >
                {type.label}
              </button>
            ))}
          </div>
        </div>

        {/* Format selection */}
        <div>
          <div className="font-mono text-sm uppercase tracking-[0.15em] text-hud-label mb-2">
            FORMAT
          </div>
          <div className="flex gap-2">
            {currentType.formats.map((fmt) => (
              <button
                key={fmt}
                onClick={() => setSelectedFormat(fmt)}
                className={`font-mono text-[13px] px-3 py-1 border transition-colors ${
                  selectedFormat === fmt
                    ? "border-accent text-accent"
                    : "border-hud-border text-hud-muted hover:text-hud-text"
                }`}
              >
                .{fmt.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex-1 py-2 bg-accent hover:bg-accent/80 disabled:opacity-50 font-mono text-[13px] uppercase tracking-wider transition-colors"
          >
            {exporting ? "EXPORTING..." : "DOWNLOAD"}
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 border border-hud-border text-hud-muted hover:text-hud-text font-mono text-[13px] uppercase tracking-wider transition-colors"
          >
            CLOSE
          </button>
        </div>
      </div>
    </div>
  );
}

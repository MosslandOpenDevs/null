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

export function ExportTab() {
  const { world, exportWorld } = useSimulationStore();
  const [selectedType, setSelectedType] = useState("wiki");
  const [selectedFormat, setSelectedFormat] = useState("md");
  const [exporting, setExporting] = useState(false);

  if (!world) return null;

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
    <div className="p-4 space-y-4">
      <div className="font-mono text-[10px] text-hud-muted">
        World: {(world.config as Record<string, unknown>)?.description
          ? String((world.config as Record<string, unknown>).description).slice(0, 80)
          : world.seed_prompt.slice(0, 80)}
      </div>

      {/* Type selection */}
      <div>
        <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-hud-label mb-2">
          DATA TYPE
        </div>
        <div className="grid grid-cols-3 gap-1">
          {EXPORT_TYPES.map((type) => (
            <button
              key={type.id}
              onClick={() => {
                setSelectedType(type.id);
                setSelectedFormat(type.formats[0]);
              }}
              className={`font-mono text-[10px] px-2 py-1.5 border transition-colors ${
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
        <div className="font-mono text-[9px] uppercase tracking-[0.15em] text-hud-label mb-2">
          FORMAT
        </div>
        <div className="flex gap-2">
          {currentType.formats.map((fmt) => (
            <button
              key={fmt}
              onClick={() => setSelectedFormat(fmt)}
              className={`font-mono text-[10px] px-3 py-1 border transition-colors ${
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

      <button
        onClick={handleExport}
        disabled={exporting}
        className="py-2 px-6 bg-accent hover:bg-accent/80 disabled:opacity-50 font-mono text-[10px] uppercase tracking-wider transition-colors"
      >
        {exporting ? "EXPORTING..." : "DOWNLOAD"}
      </button>
    </div>
  );
}

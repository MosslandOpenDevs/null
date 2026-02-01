"use client";

import { useState } from "react";
import { useSimulationStore } from "@/stores/simulation";

const STATUS_COLOR: Record<string, string> = {
  draft: "text-hud-muted",
  canon: "text-success",
  legend: "text-herald",
  disputed: "text-danger",
};

function CopyButton({ text, label }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button
      onClick={handleCopy}
      className="font-mono text-[8px] px-1.5 py-0.5 border border-hud-border text-hud-muted hover:text-accent hover:border-accent transition-colors flex-shrink-0"
      title="Copy to clipboard"
    >
      {copied ? "COPIED" : label || "📋"}
    </button>
  );
}

export function WikiTab() {
  const { wikiPages } = useSimulationStore();
  const [selectedPage, setSelectedPage] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const filtered = search
    ? wikiPages.filter((p) =>
        p.title.toLowerCase().includes(search.toLowerCase()) ||
        p.content.toLowerCase().includes(search.toLowerCase())
      )
    : wikiPages;

  const page = wikiPages.find((p) => p.id === selectedPage);

  if (page) {
    const markdown = `# ${page.title}\n\n*Status: ${page.status} | Version: ${page.version}*\n\n${page.content}`;

    return (
      <div className="p-3 space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setSelectedPage(null)}
            className="font-mono text-[9px] text-accent hover:text-accent/80 uppercase tracking-wider"
          >
            ← BACK TO INDEX
          </button>
          <CopyButton text={markdown} label="COPY MD" />
        </div>
        <div>
          <h3 className="font-mono text-sm text-hud-text font-semibold">{page.title}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={`font-mono text-[9px] uppercase ${STATUS_COLOR[page.status] || "text-hud-muted"}`}>
              {page.status}
            </span>
            <span className="font-mono text-[9px] text-hud-label">v{page.version}</span>
          </div>
        </div>
        <div className="font-mono text-[10px] text-hud-muted leading-relaxed whitespace-pre-wrap">
          {page.content}
        </div>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      {/* Search */}
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search wiki..."
        className="w-full px-2 py-1.5 bg-void border border-hud-border font-mono text-[10px] text-hud-text placeholder-hud-label focus:outline-none focus:border-hud-border-active"
      />

      {/* Page list */}
      {filtered.length === 0 ? (
        <div className="font-mono text-[10px] text-hud-label text-center py-4">
          {wikiPages.length === 0 ? "NO WIKI PAGES YET" : "NO RESULTS"}
        </div>
      ) : (
        <div className="space-y-1">
          {filtered.map((p) => (
            <div
              key={p.id}
              className="w-full text-left p-2 border border-hud-border hover:border-hud-border-active transition-colors"
            >
              <div className="flex items-center justify-between">
                <button
                  onClick={() => setSelectedPage(p.id)}
                  className="font-mono text-[11px] text-hud-text truncate text-left flex-1"
                >
                  {p.title}
                </button>
                <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                  <CopyButton
                    text={`# ${p.title}\n\n${p.content}`}
                  />
                  <span className={`font-mono text-[8px] uppercase ${STATUS_COLOR[p.status] || "text-hud-muted"}`}>
                    {p.status}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedPage(p.id)}
                className="font-mono text-[9px] text-hud-label mt-0.5 truncate block w-full text-left"
              >
                {p.content.slice(0, 80)}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

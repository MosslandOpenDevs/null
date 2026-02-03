"use client";

import { useState, useEffect, useCallback } from "react";
import { useLocale } from "next-intl";
import { useSimulationStore } from "@/stores/simulation";
import { EntityCard } from "@/components/EntityCard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

interface MentionData {
  id: string;
  mention_text: string;
  target_type: string;
  target_id: string;
  confidence: number;
}

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
      className="font-mono text-[11px] px-1.5 py-0.5 border border-hud-border text-hud-muted hover:text-accent hover:border-accent transition-colors flex-shrink-0"
      title="Copy to clipboard"
    >
      {copied ? "COPIED" : label || "📋"}
    </button>
  );
}

function HighlightedContent({
  content,
  mentions,
  worldId,
}: {
  content: string;
  mentions: MentionData[];
  worldId: string;
}) {
  const [activeEntity, setActiveEntity] = useState<{
    type: string;
    id: string;
    name: string;
    pos: { x: number; y: number };
  } | null>(null);

  if (mentions.length === 0) {
    return (
      <div className="font-sans text-sm text-hud-text leading-relaxed whitespace-pre-wrap">
        {content}
      </div>
    );
  }

  // Build highlighted text
  const parts: { text: string; mention?: MentionData }[] = [];
  let remaining = content;

  // Sort mentions by position in text (find first occurrence)
  const sortedMentions = [...mentions].sort((a, b) => {
    const posA = content.toLowerCase().indexOf(a.mention_text.toLowerCase());
    const posB = content.toLowerCase().indexOf(b.mention_text.toLowerCase());
    return posA - posB;
  });

  for (const mention of sortedMentions) {
    const idx = remaining.toLowerCase().indexOf(mention.mention_text.toLowerCase());
    if (idx === -1) continue;
    if (idx > 0) {
      parts.push({ text: remaining.slice(0, idx) });
    }
    parts.push({ text: remaining.slice(idx, idx + mention.mention_text.length), mention });
    remaining = remaining.slice(idx + mention.mention_text.length);
  }
  if (remaining) {
    parts.push({ text: remaining });
  }

  return (
    <div className="relative">
      <div className="font-sans text-sm text-hud-text leading-relaxed whitespace-pre-wrap">
        {parts.map((part, i) =>
          part.mention ? (
            <span
              key={i}
              onClick={(e) =>
                setActiveEntity({
                  type: part.mention!.target_type,
                  id: part.mention!.target_id,
                  name: part.text,
                  pos: { x: e.clientX, y: e.clientY },
                })
              }
              className="text-accent underline decoration-accent/30 cursor-pointer hover:bg-accent/10 transition-colors"
            >
              {part.text}
            </span>
          ) : (
            <span key={i}>{part.text}</span>
          )
        )}
      </div>
      {activeEntity && (
        <EntityCard
          worldId={worldId}
          entityType={activeEntity.type}
          entityId={activeEntity.id}
          entityName={activeEntity.name}
          position={activeEntity.pos}
          onClose={() => setActiveEntity(null)}
        />
      )}
    </div>
  );
}

export function WikiTab() {
  const locale = useLocale();
  const { wikiPages, world } = useSimulationStore();
  const t = (en: string, ko?: string | null) => (locale === "ko" && ko) ? ko : en;
  const [selectedPage, setSelectedPage] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [mentions, setMentions] = useState<MentionData[]>([]);

  // Fetch mentions for selected page
  useEffect(() => {
    if (!selectedPage || !world) {
      setMentions([]);
      return;
    }
    fetch(`${API_URL}/api/worlds/${world.id}/entities/wiki_page/${selectedPage}/mentions`)
      .then((r) => r.json())
      .then(setMentions)
      .catch(() => setMentions([]));
  }, [selectedPage, world]);

  const filtered = search
    ? wikiPages.filter((p) =>
        p.title.toLowerCase().includes(search.toLowerCase()) ||
        p.content.toLowerCase().includes(search.toLowerCase())
      )
    : wikiPages;

  const page = wikiPages.find((p) => p.id === selectedPage);

  if (page) {
    const displayTitle = t(page.title, page.title_ko);
    const displayContent = t(page.content, page.content_ko);
    const markdown = `# ${displayTitle}\n\n*Status: ${page.status} | Version: ${page.version}*\n\n${displayContent}`;

    return (
      <div className="p-3 space-y-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setSelectedPage(null)}
            className="font-mono text-[11px] text-accent hover:text-accent/80 uppercase tracking-wider"
          >
            ← BACK TO INDEX
          </button>
          <CopyButton text={markdown} label="COPY MD" />
        </div>
        <div>
          <h3 className="font-sans text-lg text-white font-semibold">{displayTitle}</h3>
          <div className="flex items-center gap-2 mt-1">
            <span className={`font-mono text-[11px] uppercase ${STATUS_COLOR[page.status] || "text-hud-muted"}`}>
              {page.status}
            </span>
            <span className="font-mono text-[11px] text-hud-label">v{page.version}</span>
          </div>
        </div>
        <HighlightedContent
          content={displayContent}
          mentions={mentions}
          worldId={world?.id || ""}
        />
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
        className="w-full px-2 py-1.5 bg-void border border-hud-border font-mono text-xs text-hud-text placeholder-hud-label focus:outline-none focus:border-hud-border-active"
      />

      {/* Page list */}
      {filtered.length === 0 ? (
        <div className="font-mono text-xs text-hud-label text-center py-4">
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
                  className="font-sans text-sm text-hud-text truncate text-left flex-1"
                >
                  {t(p.title, p.title_ko)}
                </button>
                <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                  <CopyButton
                    text={`# ${t(p.title, p.title_ko)}\n\n${t(p.content, p.content_ko)}`}
                  />
                  <span className={`font-mono text-[11px] uppercase ${STATUS_COLOR[p.status] || "text-hud-muted"}`}>
                    {p.status}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedPage(p.id)}
                className="font-sans text-xs text-hud-label mt-0.5 truncate block w-full text-left"
              >
                {t(p.content, p.content_ko).slice(0, 80)}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

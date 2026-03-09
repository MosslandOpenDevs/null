"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";
import { useSimulationStore } from "@/stores/simulation";
import { useMultiverseStore, GlobalSearchResult } from "@/stores/multiverse";
import { useTaxonomyStore, TaxonomyNode } from "@/stores/taxonomy";

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tagName = target.tagName.toLowerCase();
  return target.isContentEditable || tagName === "input" || tagName === "textarea" || tagName === "select";
}

export function CommandPalette() {
  const t = useTranslations("command");
  const { locale } = useParams<{ locale: string }>();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"local" | "global" | "taxonomy">("local");
  const { agents, wikiPages, setSelectedAgent, setIntelTab } = useSimulationStore();
  const { searchResults, searching, globalSearch } = useMultiverseStore();
  const { rootNodes, fetchTree } = useTaxonomyStore();
  const shortcutLabel = useMemo(() => {
    if (typeof navigator !== "undefined" && /mac/i.test(navigator.platform)) {
      return "⌘K";
    }
    return "Ctrl+K";
  }, []);

  const closePalette = useCallback(() => {
    setOpen(false);
    setQuery("");
    setMode("local");
  }, []);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const typingTarget = isTypingTarget(e.target);
      const openWithShortcut = (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k";
      const openWithSlash = e.key === "/" && !typingTarget;

      if (!open && (openWithShortcut || openWithSlash)) {
        e.preventDefault();
        setOpen(true);
        return;
      }

      if (e.key === "Escape" && open) {
        e.preventDefault();
        closePalette();
      }
    },
    [closePalette, open]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  // Trigger global search with debounce
  useEffect(() => {
    if (mode === "global" && query.length >= 2) {
      const timer = setTimeout(() => globalSearch(query), 300);
      return () => clearTimeout(timer);
    }
  }, [query, mode, globalSearch]);

  // Fetch taxonomy when mode changes
  useEffect(() => {
    if (mode === "taxonomy") {
      fetchTree();
    }
  }, [mode, fetchTree]);

  const q = query.toLowerCase();

  const filteredNodes = mode === "taxonomy" && query
    ? rootNodes.filter((n) => n.label.toLowerCase().includes(q))
    : rootNodes;

  const agentResults = mode === "local" && q
    ? agents.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          ((a.persona.role as string) || "").toLowerCase().includes(q)
      ).slice(0, 6)
    : [];

  const wikiResults = mode === "local" && q
    ? wikiPages.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.content.toLowerCase().includes(q)
      ).slice(0, 4)
    : [];

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24">
      <div
        className="absolute inset-0 bg-black/70"
        onClick={closePalette}
      />
      <div className="relative w-full max-w-lg bg-void-light border border-hud-border overflow-hidden">
        <div className="corner-mark corner-mark-tl" />
        <div className="corner-mark corner-mark-tr" />
        <div className="corner-mark corner-mark-bl" />
        <div className="corner-mark corner-mark-br" />

        {/* Mode toggle */}
        <div className="flex border-b border-hud-border">
          <button
            onClick={() => setMode("local")}
            className={`flex-1 py-1.5 font-mono text-sm uppercase tracking-[0.15em] ${
              mode === "local" ? "text-accent border-b border-accent" : "text-hud-muted"
            }`}
          >
            LOCAL (THIS WORLD)
          </button>
          <button
            onClick={() => setMode("global")}
            className={`flex-1 py-1.5 font-mono text-sm uppercase tracking-[0.15em] ${
              mode === "global" ? "text-accent border-b border-accent" : "text-hud-muted"
            }`}
          >
            GLOBAL
          </button>
          <button
            onClick={() => setMode("taxonomy")}
            className={`flex-1 py-1.5 font-mono text-sm uppercase tracking-[0.15em] ${
              mode === "taxonomy" ? "text-accent border-b border-accent" : "text-hud-muted"
            }`}
          >
            TAXONOMY
          </button>
        </div>

        <div className="flex items-center gap-3 border-b border-hud-border px-4 py-2 font-mono text-[11px] uppercase tracking-[0.15em] text-hud-label">
          <span>{t("shortcutLabel")}</span>
          <span className="text-hud-muted">{shortcutLabel} /</span>
          <span className="ml-auto text-hud-muted">esc</span>
        </div>

        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={mode === "global" ? t("globalPlaceholder") : t("placeholder")}
          className="w-full px-4 py-3 bg-transparent text-hud-text font-mono text-base placeholder-hud-label focus:outline-none"
        />

        {/* Local results */}
        {mode === "local" && (agentResults.length > 0 || wikiResults.length > 0) && (
          <div className="border-t border-hud-border max-h-64 overflow-y-auto">
            {agentResults.length > 0 && (
              <div>
                <div className="px-4 py-1 font-mono text-sm uppercase tracking-[0.15em] text-hud-label">
                  AGENTS
                </div>
                {agentResults.map((agent) => (
                  <button
                    key={agent.id}
                    onClick={() => {
                      setSelectedAgent(agent.id);
                      setIntelTab("agent");
                      setOpen(false);
                      setQuery("");
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-accent/10 flex items-center gap-3 transition-colors"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                    <div>
                      <div className="font-mono text-base text-hud-text">{agent.name}</div>
                      <div className="font-mono text-sm text-hud-muted">
                        {agent.persona.role as string}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {wikiResults.length > 0 && (
              <div>
                <div className="px-4 py-1 font-mono text-sm uppercase tracking-[0.15em] text-hud-label">
                  WIKI
                </div>
                {wikiResults.map((page) => (
                  <button
                    key={page.id}
                    onClick={() => {
                      setIntelTab("wiki");
                      setOpen(false);
                      setQuery("");
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-accent/10 flex items-center gap-3 transition-colors"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-success" />
                    <div>
                      <div className="font-mono text-base text-hud-text">{page.title}</div>
                      <div className="font-mono text-sm text-hud-muted">
                        {page.content.slice(0, 50)}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Taxonomy results */}
        {mode === "taxonomy" && (
          <div className="border-t border-hud-border max-h-64 overflow-y-auto">
            {filteredNodes.length === 0 ? (
              <div className="px-4 py-3 font-mono text-[13px] text-hud-label">
                No taxonomy nodes
              </div>
            ) : (
              filteredNodes.map((node: TaxonomyNode) => (
                <button
                  key={node.id}
                  onClick={() => {
                    // Navigate to taxonomy filter on home page
                    window.location.href = `/${locale}?taxonomy=${node.id}`;
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-accent/10 flex items-center gap-3 transition-colors"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-herald" />
                  <div className="flex-1 min-w-0">
                    <div className="font-mono text-base text-hud-text truncate">
                      {node.label}
                    </div>
                    <div className="font-mono text-sm text-hud-muted">
                      {node.member_count} members · depth {node.depth}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>
        )}

        {/* Global results */}
        {mode === "global" && (
          <div className="border-t border-hud-border max-h-64 overflow-y-auto">
            {searching && (
              <div className="px-4 py-3 font-mono text-[13px] text-hud-muted animate-pulse">
                Searching all worlds...
              </div>
            )}
            {!searching && searchResults.length === 0 && query.length >= 2 && (
              <div className="px-4 py-3 font-mono text-[13px] text-hud-label">
                No results found across worlds
              </div>
            )}
            {[...searchResults].sort((a, b) => b.score - a.score).map((result: GlobalSearchResult) => (
              <button
                key={`${result.entity_type}-${result.entity_id}`}
                onClick={() => {
                  // Navigate to the world containing the result
                  window.location.href = `/${locale}/world/${result.world_id}`;
                }}
                className="w-full px-4 py-2 text-left hover:bg-accent/10 flex items-center gap-3 transition-colors"
              >
                <div className={`w-1.5 h-1.5 rounded-full ${
                  result.entity_type === "wiki_page" ? "bg-success" :
                  result.entity_type === "agent" ? "bg-accent" : "bg-herald"
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-base text-hud-text truncate">{result.title}</span>
                    <span className="font-mono text-[11px] text-hud-label uppercase flex-shrink-0">
                      {result.entity_type.replace("_", " ")}
                    </span>
                  </div>
                  <div className="font-mono text-sm text-hud-muted truncate">
                    {result.snippet}
                  </div>
                </div>
                <span className="font-mono text-[11px] text-hud-label flex-shrink-0">
                  {(result.score * 100).toFixed(0)}%
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

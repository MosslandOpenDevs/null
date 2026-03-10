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
  const [activeIndex, setActiveIndex] = useState(0);
  const modeMeta = {
    local: { label: "LOCAL", hint: "Search agents and wiki in the current world", shortcut: "Alt+1" },
    global: { label: "GLOBAL", hint: "Search entities across worlds", shortcut: "Alt+2" },
    taxonomy: { label: "TAXONOMY", hint: "Jump into category clusters", shortcut: "Alt+3" },
  } as const;
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
    setActiveIndex(0);
  }, []);


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

  const filteredNodes = useMemo(
    () => (mode === "taxonomy" && query
      ? rootNodes.filter((n) => n.label.toLowerCase().includes(q))
      : rootNodes),
    [mode, q, query, rootNodes]
  );

  const agentResults = useMemo(
    () => (mode === "local" && q
      ? agents.filter(
          (a) =>
            a.name.toLowerCase().includes(q) ||
            ((a.persona.role as string) || "").toLowerCase().includes(q)
        ).slice(0, 6)
      : []),
    [agents, mode, q]
  );

  const wikiResults = useMemo(
    () => (mode === "local" && q
      ? wikiPages.filter(
          (p) =>
            p.title.toLowerCase().includes(q) ||
            p.content.toLowerCase().includes(q)
        ).slice(0, 4)
      : []),
    [mode, q, wikiPages]
  );

  const localResults = useMemo(
    () => [
      ...agentResults.map((agent) => ({
        id: `agent-${agent.id}`,
        type: "agent" as const,
        label: agent.name,
        sublabel: (agent.persona.role as string) || "",
        onSelect: () => {
          setSelectedAgent(agent.id);
          setIntelTab("agent");
          closePalette();
        },
      })),
      ...wikiResults.map((page) => ({
        id: `wiki-${page.id}`,
        type: "wiki" as const,
        label: page.title,
        sublabel: page.content.slice(0, 50),
        onSelect: () => {
          setIntelTab("wiki");
          closePalette();
        },
      })),
    ],
    [agentResults, closePalette, setIntelTab, setSelectedAgent, wikiResults]
  );

  const taxonomyResults = useMemo(
    () => filteredNodes.map((node) => ({
      id: `taxonomy-${node.id}`,
      type: "taxonomy" as const,
      label: node.label,
      sublabel: `${node.member_count} members · depth ${node.depth}`,
      onSelect: () => {
        window.location.href = `/${locale}?taxonomy=${node.id}`;
      },
    })),
    [filteredNodes, locale]
  );

  const globalResults = useMemo(
    () => [...searchResults].sort((a, b) => b.score - a.score).map((result) => ({
      id: `global-${result.entity_type}-${result.entity_id}`,
      type: "global" as const,
      label: result.title,
      sublabel: result.snippet,
      badge: result.entity_type.replace("_", " "),
      meta: `${(result.score * 100).toFixed(0)}%`,
      entityType: result.entity_type,
      onSelect: () => {
        window.location.href = `/${locale}/world/${result.world_id}`;
      },
    })),
    [locale, searchResults]
  );

  const navigableResults = mode === "local"
    ? localResults
    : mode === "taxonomy"
      ? taxonomyResults
      : globalResults;

  useEffect(() => {
    setActiveIndex(0);
  }, [mode, query]);

  useEffect(() => {
    if (navigableResults.length === 0) {
      setActiveIndex(0);
      return;
    }

    setActiveIndex((current) => Math.min(current, navigableResults.length - 1));
  }, [navigableResults]);

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
        return;
      }

      if (open && e.altKey && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
        if (e.key === "1") {
          e.preventDefault();
          setMode("local");
          return;
        }
        if (e.key === "2") {
          e.preventDefault();
          setMode("global");
          return;
        }
        if (e.key === "3") {
          e.preventDefault();
          setMode("taxonomy");
          return;
        }
      }

      if (!open || navigableResults.length === 0) {
        return;
      }

      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIndex((current) => (current + 1) % navigableResults.length);
        return;
      }

      if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIndex((current) => (current - 1 + navigableResults.length) % navigableResults.length);
        return;
      }

      if (e.key === "Enter") {
        e.preventDefault();
        navigableResults[activeIndex]?.onSelect();
      }
    },
    [activeIndex, closePalette, navigableResults, open]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

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
            title={`${modeMeta.local.label} · ${modeMeta.local.shortcut}`}
            className={`flex-1 py-1.5 font-mono text-sm uppercase tracking-[0.15em] ${
              mode === "local" ? "text-accent border-b border-accent" : "text-hud-muted"
            }`}
          >
            LOCAL (THIS WORLD)
          </button>
          <button
            onClick={() => setMode("global")}
            title={`${modeMeta.global.label} · ${modeMeta.global.shortcut}`}
            className={`flex-1 py-1.5 font-mono text-sm uppercase tracking-[0.15em] ${
              mode === "global" ? "text-accent border-b border-accent" : "text-hud-muted"
            }`}
          >
            GLOBAL
          </button>
          <button
            onClick={() => setMode("taxonomy")}
            title={`${modeMeta.taxonomy.label} · ${modeMeta.taxonomy.shortcut}`}
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
          <span className="text-hud-muted">{modeMeta.local.shortcut}</span>
          <span className="text-hud-muted">{modeMeta.global.shortcut}</span>
          <span className="text-hud-muted">{modeMeta.taxonomy.shortcut}</span>
          <span className="ml-auto text-hud-muted">esc</span>
        </div>

        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={mode === "global" ? t("globalPlaceholder") : t("placeholder")}
          className="w-full px-4 py-3 bg-transparent text-hud-text font-mono text-base placeholder-hud-label focus:outline-none"
        />

        {!query && (
          <div className="border-t border-hud-border px-4 py-3 grid gap-2 bg-black/10">
            <div className="font-mono text-[11px] uppercase tracking-[0.15em] text-hud-label">
              Quick modes
            </div>
            <div className="grid gap-2">
              {(["local", "global", "taxonomy"] as const).map((modeKey) => {
                const meta = modeMeta[modeKey];
                const isActive = mode === modeKey;
                return (
                  <button
                    key={modeKey}
                    type="button"
                    onClick={() => setMode(modeKey)}
                    className={`flex items-center justify-between gap-3 rounded border px-3 py-2 text-left transition-colors ${
                      isActive
                        ? "border-accent bg-accent/10 text-hud-text"
                        : "border-hud-border text-hud-muted hover:border-hud-border-active hover:text-hud-text"
                    }`}
                  >
                    <div>
                      <div className="font-mono text-[13px] uppercase tracking-[0.14em]">{meta.label}</div>
                      <div className="font-mono text-[12px] normal-case tracking-normal">{meta.hint}</div>
                    </div>
                    <span className="font-mono text-[11px] uppercase tracking-[0.14em]">{meta.shortcut}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Local results */}
        {mode === "local" && (agentResults.length > 0 || wikiResults.length > 0) && (
          <div className="border-t border-hud-border max-h-64 overflow-y-auto">
            {agentResults.length > 0 && (
              <div>
                <div className="px-4 py-1 font-mono text-sm uppercase tracking-[0.15em] text-hud-label">
                  AGENTS
                </div>
                {agentResults.map((agent, index) => {
                  const isActive = activeIndex === index;
                  return (
                    <button
                      key={agent.id}
                      onClick={() => {
                        setSelectedAgent(agent.id);
                        setIntelTab("agent");
                        closePalette();
                      }}
                      className={`w-full px-4 py-2 text-left flex items-center gap-3 transition-colors ${
                        isActive ? "bg-accent/15" : "hover:bg-accent/10"
                      }`}
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                      <div>
                        <div className="font-mono text-base text-hud-text">{agent.name}</div>
                        <div className="font-mono text-sm text-hud-muted">
                          {agent.persona.role as string}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            {wikiResults.length > 0 && (
              <div>
                <div className="px-4 py-1 font-mono text-sm uppercase tracking-[0.15em] text-hud-label">
                  WIKI
                </div>
                {wikiResults.map((page, index) => {
                  const isActive = activeIndex === agentResults.length + index;
                  return (
                    <button
                      key={page.id}
                      onClick={() => {
                        setIntelTab("wiki");
                        closePalette();
                      }}
                      className={`w-full px-4 py-2 text-left flex items-center gap-3 transition-colors ${
                        isActive ? "bg-accent/15" : "hover:bg-accent/10"
                      }`}
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-success" />
                      <div>
                        <div className="font-mono text-base text-hud-text">{page.title}</div>
                        <div className="font-mono text-sm text-hud-muted">
                          {page.content.slice(0, 50)}
                        </div>
                      </div>
                    </button>
                  );
                })}
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
              filteredNodes.map((node: TaxonomyNode, index) => {
                const isActive = activeIndex === index;
                return (
                  <button
                    key={node.id}
                    onClick={() => {
                      window.location.href = `/${locale}?taxonomy=${node.id}`;
                    }}
                    className={`w-full px-4 py-2 text-left flex items-center gap-3 transition-colors ${
                      isActive ? "bg-accent/15" : "hover:bg-accent/10"
                    }`}
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
                );
              })
            )}
          </div>
        )}

        {/* Global results */}
        {mode === "global" && (
          <div className="border-t border-hud-border max-h-64 overflow-y-auto">
            {query.length < 2 && (
              <div className="px-4 py-3 font-mono text-[13px] text-hud-label">
                Type at least 2 characters to search across worlds
              </div>
            )}
            {query.length >= 2 && searching && (
              <div className="px-4 py-3 font-mono text-[13px] text-hud-muted animate-pulse">
                Searching all worlds...
              </div>
            )}
            {query.length >= 2 && !searching && globalResults.length === 0 && (
              <div className="px-4 py-3 font-mono text-[13px] text-hud-label">
                No results found across worlds
              </div>
            )}
            {query.length >= 2 && globalResults.map((result, index) => {
              const isActive = activeIndex === index;
              return (
                <button
                  key={result.id}
                  onClick={result.onSelect}
                  className={`w-full px-4 py-2 text-left flex items-center gap-3 transition-colors ${
                    isActive ? "bg-accent/15" : "hover:bg-accent/10"
                  }`}
                >
                  <div className={`w-1.5 h-1.5 rounded-full ${
                    result.entityType === "wiki_page" ? "bg-success" :
                    result.entityType === "agent" ? "bg-accent" : "bg-herald"
                  }`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-base text-hud-text truncate">{result.label}</span>
                      <span className="font-mono text-[11px] text-hud-label uppercase flex-shrink-0">
                        {result.badge}
                      </span>
                    </div>
                    <div className="font-mono text-sm text-hud-muted truncate">
                      {result.sublabel}
                    </div>
                  </div>
                  <span className="font-mono text-[11px] text-hud-label flex-shrink-0">
                    {result.meta}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

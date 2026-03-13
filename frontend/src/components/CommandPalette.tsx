"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";
import { useSimulationStore } from "@/stores/simulation";
import { useMultiverseStore, GlobalSearchResult } from "@/stores/multiverse";
import { useTaxonomyStore, TaxonomyNode } from "@/stores/taxonomy";

const COMMAND_MODE_STORAGE_KEY = "null-command-palette-mode";
const RECENT_QUERY_STORAGE_KEY = "null-command-palette-recent-queries";
const RECENT_QUERY_LIMIT = 5;

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
  const [recentQueries, setRecentQueries] = useState<Record<"local" | "global" | "taxonomy", string[]>>({
    local: [],
    global: [],
    taxonomy: [],
  });
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

  const persistRecentQuery = useCallback((value: string, selectedMode = mode) => {
    const normalizedQuery = value.trim();
    if (normalizedQuery.length < 2) {
      return;
    }

    setRecentQueries((current) => ({
      ...current,
      [selectedMode]: [normalizedQuery, ...current[selectedMode].filter((entry) => entry !== normalizedQuery)].slice(0, RECENT_QUERY_LIMIT),
    }));
  }, [mode]);

  const closePalette = useCallback(() => {
    persistRecentQuery(query);
    setOpen(false);
    setQuery("");
    setActiveIndex(0);
  }, [persistRecentQuery, query]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const storedMode = window.localStorage.getItem(COMMAND_MODE_STORAGE_KEY);
    if (storedMode === "local" || storedMode === "global" || storedMode === "taxonomy") {
      setMode(storedMode);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    try {
      const rawRecentQueries = window.localStorage.getItem(RECENT_QUERY_STORAGE_KEY);
      if (!rawRecentQueries) {
        return;
      }

      const parsed = JSON.parse(rawRecentQueries);
      setRecentQueries({
        local: Array.isArray(parsed?.local) ? parsed.local.filter((value: unknown): value is string => typeof value === "string").slice(0, RECENT_QUERY_LIMIT) : [],
        global: Array.isArray(parsed?.global) ? parsed.global.filter((value: unknown): value is string => typeof value === "string").slice(0, RECENT_QUERY_LIMIT) : [],
        taxonomy: Array.isArray(parsed?.taxonomy) ? parsed.taxonomy.filter((value: unknown): value is string => typeof value === "string").slice(0, RECENT_QUERY_LIMIT) : [],
      });
    } catch {
      window.localStorage.removeItem(RECENT_QUERY_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(COMMAND_MODE_STORAGE_KEY, mode);
  }, [mode]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(RECENT_QUERY_STORAGE_KEY, JSON.stringify(recentQueries));
  }, [recentQueries]);

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

  const resultsSummary = useMemo(() => {
    if (mode === "global") {
      if (query.length < 2) return "Type 2+ characters to search across worlds";
      if (searching) return "Searching across worlds…";
      return `${globalResults.length} result${globalResults.length === 1 ? "" : "s"}`;
    }

    if (mode === "taxonomy") {
      return `${filteredNodes.length} taxonomy node${filteredNodes.length === 1 ? "" : "s"}`;
    }

    return `${localResults.length} local match${localResults.length === 1 ? "" : "es"}`;
  }, [filteredNodes.length, globalResults.length, localResults.length, mode, query.length, searching]);

  const emptyStateActions = useMemo(() => {
    if (!query) {
      return [] as { label: string; description: string; onClick: () => void }[];
    }

    const actions = [
      {
        label: "Clear query",
        description: "Reset the search and keep this mode open",
        onClick: () => {
          setQuery("");
          setActiveIndex(0);
        },
      },
    ];

    if (mode !== "local") {
      actions.push({
        label: "Try local mode",
        description: "Search agents and wiki in the current world",
        onClick: () => {
          setMode("local");
          setActiveIndex(0);
        },
      });
    }

    if (mode !== "global") {
      actions.push({
        label: "Try global mode",
        description: "Search entities across every world",
        onClick: () => {
          setMode("global");
          setActiveIndex(0);
        },
      });
    }

    if (mode !== "taxonomy") {
      actions.push({
        label: "Try taxonomy mode",
        description: "Jump through category clusters instead",
        onClick: () => {
          setMode("taxonomy");
          setActiveIndex(0);
        },
      });
    }

    return actions;
  }, [mode, query]);

  const modeRecentQueries = recentQueries[mode];

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
        persistRecentQuery(query);
        navigableResults[activeIndex]?.onSelect();
      }
    },
    [activeIndex, closePalette, navigableResults, open, persistRecentQuery, query]
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

        <div className="flex items-center justify-between gap-3 border-b border-hud-border px-4 py-2 font-mono text-[11px] uppercase tracking-[0.14em] text-hud-label bg-black/10">
          <span className="truncate">{modeMeta[mode].hint}</span>
          <span className="text-hud-muted whitespace-nowrap">{resultsSummary}</span>
        </div>

        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={mode === "global" ? t("globalPlaceholder") : t("placeholder")}
          className="w-full px-4 py-3 bg-transparent text-hud-text font-mono text-base placeholder-hud-label focus:outline-none"
        />

        {!query && (
          <div className="border-t border-hud-border px-4 py-3 grid gap-3 bg-black/10">
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.15em] text-hud-label">
                Quick modes
              </div>
              <div className="mt-2 grid gap-2">
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

            {modeRecentQueries.length > 0 && (
              <div className="grid gap-2">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-mono text-[11px] uppercase tracking-[0.15em] text-hud-label">
                    Recent in {modeMeta[mode].label}
                  </div>
                  <button
                    type="button"
                    onClick={() => setRecentQueries((current) => ({ ...current, [mode]: [] }))}
                    className="font-mono text-[10px] uppercase tracking-[0.15em] text-hud-muted transition-colors hover:text-hud-text"
                  >
                    Clear
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {modeRecentQueries.map((recentQuery) => (
                    <div
                      key={`${mode}-${recentQuery}`}
                      className="inline-flex items-center overflow-hidden rounded-full border border-hud-border text-hud-muted transition-colors hover:border-hud-border-active"
                    >
                      <button
                        type="button"
                        onClick={() => {
                          setQuery(recentQuery);
                          setActiveIndex(0);
                        }}
                        className="px-3 py-1.5 font-mono text-[11px] transition-colors hover:text-hud-text"
                        title={`Reuse recent ${modeMeta[mode].label.toLowerCase()} search`}
                      >
                        {recentQuery}
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setRecentQueries((current) => ({
                            ...current,
                            [mode]: current[mode].filter((entry) => entry !== recentQuery),
                          }));
                        }}
                        className="border-l border-hud-border px-2 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors hover:bg-white/5 hover:text-hud-text"
                        title={`Remove ${recentQuery} from recent ${modeMeta[mode].label.toLowerCase()} searches`}
                        aria-label={`Remove ${recentQuery} from recent ${modeMeta[mode].label.toLowerCase()} searches`}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {query && navigableResults.length === 0 && !(mode === "global" && (query.length < 2 || searching)) && (
          <div className="border-t border-hud-border px-4 py-3 grid gap-3 bg-black/10">
            <div className="font-mono text-[13px] text-hud-label">
              {mode === "local"
                ? "No agents or wiki pages matched this world search"
                : mode === "taxonomy"
                  ? "No taxonomy nodes matched this filter"
                  : "No results found across worlds"}
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {emptyStateActions.map((action) => (
                <button
                  key={action.label}
                  type="button"
                  onClick={action.onClick}
                  className="rounded border border-hud-border px-3 py-2 text-left transition-colors text-hud-muted hover:border-hud-border-active hover:text-hud-text"
                >
                  <div className="font-mono text-[12px] uppercase tracking-[0.14em] text-hud-text">{action.label}</div>
                  <div className="mt-1 font-mono text-[12px] normal-case tracking-normal">{action.description}</div>
                </button>
              ))}
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
              query ? null : (
                <div className="px-4 py-3 font-mono text-[13px] text-hud-label">
                  No taxonomy nodes
                </div>
              )
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

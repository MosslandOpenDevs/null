"use client";

import { useTranslations } from "next-intl";
import { useState, useEffect, useRef, useMemo } from "react";
import { useParams } from "next/navigation";
import { useSimulationStore, WorldData } from "@/stores/simulation";
import { CommandPalette } from "@/components/CommandPalette";
import { TaxonomyTreeMap } from "@/components/TaxonomyTreeMap";
import { BookmarkDrawer } from "@/components/BookmarkDrawer";
import { WorldCard } from "@/components/WorldCard";
import { IncubatorChip } from "@/components/IncubatorChip";
import { useBookmarkStore } from "@/stores/bookmarks";
import { LocaleToggle } from "@/components/LocaleToggle";
import { useTaxonomyStore } from "@/stores/taxonomy";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

const INITIAL_EXAMPLES = [
  "Neon Joseon — 1700년대 조선이 증기기관을 발명한 대체역사. 왕실, 상인 길드, 비밀 학자 결사, 농민 반란군이 권력을 두고 경쟁한다.",
  "Deep Ocean Civilization — Sentient species evolve in ocean trenches. Bioluminescent cities, thermal vent economies, pressure-based caste systems.",
  "AI Pantheon — In 2089, seven superintelligent AIs govern humanity. Each has a different ethical framework. They debate, scheme, and negotiate the fate of billions.",
  "거꾸로 된 바벨탑 — 모든 인류가 하나의 언어를 쓰던 시대. 한 이단 집단이 '다름'을 발명하려 한다.",
  "Floating Archipelago — Islands drift across an endless sky. Nomadic traders, sky-pirates, cloud-miners, and the mysterious Order of the Compass.",
  "Silicon Renaissance — Florence, 1492. But instead of paint, Michelangelo sculpts with programmable matter. The Medici fund neural networks.",
  "Mycelium Network — A planet where fungal networks are sentient. Surface creatures are pawns. Underground, ancient mycelia wage slow wars spanning millennia.",
  "사이버 삼국지 — 2150년 한반도, 세 개의 메가코퍼레이션이 통일을 두고 사이버 전쟁. 해커 용병, AI 참모, 디지털 난민.",
  "The Last Library — Reality is collapsing. Factions of librarians guard different versions of history. What they preserve becomes real. What they forget, vanishes.",
  "Quantum Diplomacy — Parallel universes can now communicate. Ambassadors negotiate between realities. Some want merging, some want isolation, some want conquest.",
  "Mars Colony Year 50 — The first generation born on Mars wants independence. Earth corporations say no. Underground resistance meets corporate mercenaries.",
  "꿈의 시장 — 사람들이 꿈을 사고파는 세계. 악몽 딜러, 꿈 도둑, 꿈을 잃어버린 사람들의 혁명.",
  "Eternal Empire — A civilization that discovered immortality 10,000 years ago. Stagnation, underground mortality cults, and the 'Last Child' prophecy.",
  "Symbiont Wars — Every human bonds with an alien parasite that grants powers but slowly changes their personality. Purists vs Bonded vs the Hive.",
  "언더그라운드 서울 — 지표면이 오염되어 서울 지하 도시에서 100만명이 생존. 구역 간 영토 분쟁, 지상 탐험가, 정수 길드.",
  "Post-Music World — Sound itself has become weaponized. Silence zones are sanctuaries. Composers are generals. A deaf child may hold the key to peace.",
  "Living Architecture — Buildings are biological organisms. Architects are surgeons. A building revolution is brewing — the structures want rights.",
  "시간 난민 — 과거에서 온 사람들이 2200년에 난민 수용소에 모인다. 조선시대 선비, 로마 병사, 빅토리아 시대 과학자가 함께 생존.",
  "Infinite Casino — Reality is a game run by cosmic entities. Civilizations bet their existence. Cheaters are executed across all timelines.",
  "Ghost Internet — The dead can post online. Their social media persists and evolves. A corporation monetizes the afterlife. The living protest.",
];

export default function HomePage() {
  const t = useTranslations();
  const { locale } = useParams<{ locale: string }>();
  const [seedPrompt, setSeedPrompt] = useState("");
  const [creating, setCreating] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [examples, setExamples] = useState<string[]>(INITIAL_EXAMPLES);
  const [exampleIndex, setExampleIndex] = useState(0);
  const [displayedExample, setDisplayedExample] = useState("");
  const [isTyping, setIsTyping] = useState(true);
  const fetchedCount = useRef(0);
  const { createWorld, autoWorlds, fetchAutoWorlds, worldTags, tagFilter, setTagFilter } = useSimulationStore();
  const { setDrawerOpen } = useBookmarkStore();
  const { fetchNode } = useTaxonomyStore();
  const [taxonomyWorldFilter, setTaxonomyWorldFilter] = useState<string | null>(null);
  const [taxonomyWorlds, setTaxonomyWorlds] = useState<Array<{ id: string; seed_prompt: string; status: string }>>([]);

  // Split worlds into mature (Observatory) vs actively incubating
  const { matureWorlds, incubatingWorlds } = useMemo(() => {
    const mature: WorldData[] = [];
    const incubating: WorldData[] = [];
    for (const w of autoWorlds) {
      const convCount = w.conversation_count ?? 0;
      const wikiCount = w.wiki_page_count ?? 0;
      const isMature = convCount >= 5 && wikiCount >= 1;
      if (isMature) {
        mature.push(w);
      } else if (w.status === "generating" || w.status === "running") {
        // Only show actively running/generating worlds in incubator
        incubating.push(w);
      }
    }
    return { matureWorlds: mature, incubatingWorlds: incubating };
  }, [autoWorlds]);

  // Collect all unique tags from worlds
  const allTags = useMemo(() => {
    const tagSet = new Map<string, number>();
    Object.values(worldTags).forEach((tags) => {
      tags.forEach((t) => {
        tagSet.set(t.tag, (tagSet.get(t.tag) || 0) + 1);
      });
    });
    return Array.from(tagSet.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 20);
  }, [worldTags]);

  // Fetch fresh AI-generated examples every time we cycle through existing ones
  useEffect(() => {
    if (exampleIndex > 0 && exampleIndex % 5 === 0) {
      fetchedCount.current++;
      fetch(`${API_URL}/api/seeds`)
        .then((r) => r.json())
        .then((newSeeds: string[]) => {
          if (Array.isArray(newSeeds) && newSeeds.length > 0) {
            setExamples((prev) => [...prev, ...newSeeds]);
          }
        })
        .catch(() => {});
    }
  }, [exampleIndex]);

  // Typewriter effect for examples
  useEffect(() => {
    const target = examples[exampleIndex % examples.length];
    if (!target) return;
    if (isTyping) {
      if (displayedExample.length < target.length) {
        const timer = setTimeout(() => {
          setDisplayedExample(target.slice(0, displayedExample.length + 1));
        }, 25);
        return () => clearTimeout(timer);
      } else {
        const timer = setTimeout(() => setIsTyping(false), 3000);
        return () => clearTimeout(timer);
      }
    } else {
      if (displayedExample.length > 0) {
        const timer = setTimeout(() => {
          setDisplayedExample(displayedExample.slice(0, -2));
        }, 10);
        return () => clearTimeout(timer);
      } else {
        setExampleIndex((i) => i + 1);
        setIsTyping(true);
      }
    }
  }, [displayedExample, isTyping, exampleIndex, examples]);

  // Fetch auto-generated worlds periodically
  useEffect(() => {
    fetchAutoWorlds();
    const interval = setInterval(fetchAutoWorlds, 10000);
    return () => clearInterval(interval);
  }, [fetchAutoWorlds]);

  const handleCreate = async () => {
    if (!seedPrompt.trim()) return;
    setCreating(true);
    try {
      await createWorld(seedPrompt);
      setSeedPrompt("");
      setToast("World queued — check the Incubator");
      setTimeout(() => setToast(null), 4000);
    } finally {
      setCreating(false);
    }
  };

  const handleExampleClick = () => {
    setSeedPrompt(examples[exampleIndex % examples.length]);
  };

  return (
    <main className="flex flex-col items-center min-h-screen p-8">
      <div className="fixed top-4 right-4 z-40">
        <LocaleToggle />
      </div>
      <h1 className="text-4xl font-bold mb-2 tracking-tight">
        {t("app.title")}
      </h1>
      <p className="text-hud-muted mb-8">{t("app.subtitle")}</p>

      {/* Toast */}
      {toast && (
        <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-accent text-void font-mono text-base uppercase tracking-wider rounded shadow-lg">
          {toast}
        </div>
      )}

      {/* ===== OBSERVATORY — Mature worlds (TOP, hero section) ===== */}
      {matureWorlds.length > 0 && (
        <div className="w-full max-w-5xl mb-12">
          <h2 className="text-base uppercase tracking-widest text-hud-label mb-4">
            Observatory — Mature Worlds
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {matureWorlds.map((w) => (
              <WorldCard key={w.id} world={w} locale={locale} />
            ))}
          </div>
        </div>
      )}

      {/* Empty state when no mature worlds */}
      {matureWorlds.length === 0 && (
        <div className="w-full max-w-5xl mb-12 py-12 text-center border border-dashed border-hud-border rounded-lg">
          <div className="font-mono text-base text-hud-muted mb-1">NO MATURE WORLDS YET</div>
          <div className="font-mono text-sm text-hud-label">
            Worlds need 5+ conversations and 1+ wiki page to appear here
          </div>
        </div>
      )}

      {/* ===== INCUBATOR — Only generating/running worlds ===== */}
      {incubatingWorlds.length > 0 && (
        <div className="w-full max-w-5xl mb-12">
          <h2 className="text-base uppercase tracking-widest text-hud-label mb-3">
            Incubator — Active
          </h2>
          <div className="flex flex-wrap gap-2">
            {incubatingWorlds.map((w) => (
              <IncubatorChip key={w.id} world={w} locale={locale} />
            ))}
          </div>
        </div>
      )}

      {/* ===== Tag filter ===== */}
      {allTags.length > 0 && (
        <div className="w-full max-w-5xl mb-8">
          <h2 className="text-base uppercase tracking-widest text-hud-label mb-3">
            Filter by tag
          </h2>
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setTagFilter(null)}
              className={`px-2.5 py-1 rounded text-[13px] font-mono uppercase tracking-wider border transition-colors ${
                !tagFilter
                  ? "border-accent text-accent bg-accent/10"
                  : "border-hud-border text-hud-muted hover:text-hud-text hover:border-hud-border-active"
              }`}
            >
              ALL
            </button>
            {allTags.map(([tag, count]) => (
              <button
                key={tag}
                onClick={() => setTagFilter(tagFilter === tag ? null : tag)}
                className={`px-2.5 py-1 rounded text-[13px] font-mono uppercase tracking-wider border transition-colors ${
                  tagFilter === tag
                    ? "border-accent text-accent bg-accent/10"
                    : "border-hud-border text-hud-muted hover:text-hud-text hover:border-hud-border-active"
                }`}
              >
                {tag} ({count})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ===== Taxonomy TreeMap ===== */}
      <div className="w-full max-w-5xl mb-8">
        <TaxonomyTreeMap
          onSelectNode={async (nodeId) => {
            setTaxonomyWorldFilter(nodeId);
            try {
              const resp = await fetch(`${API_URL}/api/taxonomy/tree/${nodeId}/worlds`);
              if (resp.ok) {
                setTaxonomyWorlds(await resp.json());
              }
            } catch {
              setTaxonomyWorlds([]);
            }
          }}
        />
      </div>

      {/* Taxonomy-filtered worlds */}
      {taxonomyWorldFilter && taxonomyWorlds.length > 0 && (
        <div className="w-full max-w-5xl mb-8">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-base uppercase tracking-widest text-hud-label">
              Worlds in category
            </h2>
            <button
              onClick={() => {
                setTaxonomyWorldFilter(null);
                setTaxonomyWorlds([]);
              }}
              className="text-sm font-mono text-hud-muted hover:text-accent uppercase"
            >
              CLEAR
            </button>
          </div>
          <div className="space-y-1">
            {taxonomyWorlds.map((w) => (
              <a
                key={w.id}
                href={`/${locale}/world/${w.id}`}
                className="block px-4 py-2 rounded-lg border border-accent/30 bg-accent/5 hover:bg-accent/10 transition-all"
              >
                <p className="text-base text-hud-text truncate">{w.seed_prompt}</p>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* ===== CREATE WORLD (bottom — secondary action) ===== */}
      <div className="w-full max-w-2xl space-y-4 mt-4 pt-8 border-t border-hud-border/50">
        <h2 className="text-base uppercase tracking-widest text-hud-label mb-2 text-center">
          Launch New World
        </h2>

        <button
          onClick={handleExampleClick}
          className="w-full text-left px-4 py-3 rounded-lg border border-hud-border bg-void-light/50 hover:border-accent/50 transition-colors group"
        >
          <span className="text-[13px] uppercase tracking-widest text-hud-label group-hover:text-accent/70">
            Example — click to use
          </span>
          <p className="text-base text-hud-muted mt-1 min-h-[2.5rem]">
            {displayedExample}
            <span className="inline-block w-[2px] h-4 bg-accent/70 ml-0.5 animate-pulse align-middle" />
          </p>
        </button>

        <textarea
          value={seedPrompt}
          onChange={(e) => setSeedPrompt(e.target.value)}
          placeholder={t("world.seedPlaceholder")}
          className="w-full h-32 bg-void-light border border-hud-border rounded-lg p-4 text-hud-text placeholder-hud-muted focus:border-accent focus:outline-none resize-none"
        />
        <button
          onClick={handleCreate}
          disabled={creating || !seedPrompt.trim()}
          className="w-full py-3 bg-accent hover:bg-accent/80 disabled:opacity-50 rounded-lg font-semibold transition-colors"
        >
          {creating ? "Queuing genesis..." : t("world.create")}
        </button>
      </div>

      <CommandPalette />
      <BookmarkDrawer />

      {/* Bookmark toggle button */}
      <button
        onClick={() => setDrawerOpen(true)}
        className="fixed right-4 bottom-4 z-40 px-3 py-2 bg-void-light border border-hud-border hover:border-accent font-mono text-sm text-hud-muted hover:text-accent uppercase tracking-wider transition-colors"
      >
        BOOKMARKS
      </button>
    </main>
  );
}

"use client";

import { useEffect, useCallback, useRef } from "react";
import { useLocale } from "next-intl";
import { useSimulationStore } from "@/stores/simulation";
import { AgentAvatar } from "./AgentAvatar";

export function FeedTab() {
  const locale = useLocale();
  const { world, feedItems, fetchFeed, setSelectedConversation, setIntelTab, fetchConversations } =
    useSimulationStore();
  const sentinelRef = useRef<HTMLDivElement>(null);
  const loadingRef = useRef(false);

  const t = (en: string, ko?: string | null) =>
    locale === "ko" && ko ? ko : en;

  useEffect(() => {
    if (world?.id) {
      fetchFeed(world.id);
      fetchConversations(world.id);
    }
  }, [world?.id]);

  // Infinite scroll
  const loadMore = useCallback(() => {
    if (!world?.id || loadingRef.current || feedItems.length === 0) return;
    const oldest = feedItems[feedItems.length - 1]?.created_at;
    if (!oldest) return;
    loadingRef.current = true;
    fetchFeed(world.id, oldest).finally(() => {
      loadingRef.current = false;
    });
  }, [world?.id, feedItems, fetchFeed]);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore();
      },
      { threshold: 0.1 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [loadMore]);

  if (!world) return null;

  if (feedItems.length === 0) {
    return (
      <div className="flex items-center justify-center h-48">
        <span className="font-sans text-sm text-hud-muted">
          No activity yet. The world is still waking up...
        </span>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-2">
      {feedItems.map((item, i) => {
        if (item.type === "conversation") {
          return (
            <ConversationCard
              key={`conv-${item.data.id || i}`}
              data={item.data}
              createdAt={item.created_at}
              locale={locale}
              t={t}
              onClick={() => {
                setSelectedConversation(item.data.id as string);
              }}
            />
          );
        }
        if (item.type === "wiki_edit") {
          return (
            <WikiEditCard
              key={`wiki-${item.data.id || i}`}
              data={item.data}
              createdAt={item.created_at}
              t={t}
              onClick={() => setIntelTab("wiki")}
            />
          );
        }
        if (item.type === "epoch") {
          return (
            <EpochCard
              key={`epoch-${item.data.epoch || i}`}
              data={item.data}
              t={t}
            />
          );
        }
        return null;
      })}
      <div ref={sentinelRef} className="h-8" />
    </div>
  );
}

function ConversationCard({
  data,
  createdAt,
  locale,
  t,
  onClick,
}: {
  data: Record<string, unknown>;
  createdAt: string | null;
  locale: string;
  t: (en: string, ko?: string | null) => string;
  onClick: () => void;
}) {
  const topic = t(data.topic as string, data.topic_ko as string | undefined);
  const names = (data.participant_names as string[]) || [];
  const msgCount = (data.message_count as number) || 0;
  const preview = (data.first_message_preview as string) || "";

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 border border-hud-border hover:border-accent/40 hover:bg-accent/5 transition-colors rounded"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="font-sans text-sm font-semibold text-hud-text leading-snug flex-1">
          {topic}
        </h4>
        <span className="font-mono text-xs text-accent flex-shrink-0">
          {msgCount} msg
        </span>
      </div>
      <div className="flex items-center gap-1 mb-2">
        {names.slice(0, 3).map((name, i) => (
          <AgentAvatar key={i} name={name} size="sm" />
        ))}
        {names.length > 3 && (
          <span className="font-mono text-[11px] text-hud-muted">
            +{names.length - 3}
          </span>
        )}
      </div>
      {preview && (
        <p className="font-sans text-xs text-hud-muted line-clamp-2 leading-relaxed">
          {preview}
        </p>
      )}
      {createdAt && (
        <div className="font-mono text-[11px] text-hud-label mt-2">
          {new Date(createdAt).toLocaleString()}
        </div>
      )}
    </button>
  );
}

function WikiEditCard({
  data,
  createdAt,
  t,
  onClick,
}: {
  data: Record<string, unknown>;
  createdAt: string | null;
  t: (en: string, ko?: string | null) => string;
  onClick: () => void;
}) {
  const title = t(data.title as string, data.title_ko as string | undefined);
  const agentName = data.agent_name as string | null;
  const status = data.status as string;

  const statusColor: Record<string, string> = {
    draft: "text-hud-muted border-hud-muted/30",
    canon: "text-success border-success/30",
    legend: "text-herald border-herald/30",
    disputed: "text-danger border-danger/30",
  };

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 border border-hud-border hover:border-success/40 hover:bg-success/5 transition-colors rounded"
    >
      <div className="flex items-center gap-2">
        <span className="font-mono text-[11px] text-success uppercase">WIKI</span>
        <span className="font-sans text-sm text-hud-text flex-1 truncate">
          {agentName ? `${agentName} updated ` : ""}<span className="font-semibold text-hud-text">{title}</span>
        </span>
        <span
          className={`font-mono text-[11px] px-1.5 py-0.5 border rounded uppercase ${statusColor[status] || "text-hud-muted border-hud-border"}`}
        >
          {status}
        </span>
      </div>
      {createdAt && (
        <div className="font-mono text-[11px] text-hud-label mt-1">
          {new Date(createdAt).toLocaleString()}
        </div>
      )}
    </button>
  );
}

function EpochCard({
  data,
  t,
}: {
  data: Record<string, unknown>;
  t: (en: string, ko?: string | null) => string;
}) {
  const summary = t(data.summary as string, data.summary_ko as string | undefined);
  const themeCount = (data.theme_count as number) || 0;

  return (
    <div className="epoch-line my-3">
      <span className="whitespace-nowrap">
        EPOCH {data.epoch as number}
        {themeCount > 0 && (
          <span className="text-hud-muted ml-2 normal-case text-[11px]">
            {themeCount} themes
          </span>
        )}
      </span>
    </div>
  );
}

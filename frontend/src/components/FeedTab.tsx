"use client";

import { useEffect, useCallback, useRef } from "react";
import { useLocale } from "next-intl";
import { useSimulationStore } from "@/stores/simulation";
import { AgentAvatar } from "./AgentAvatar";

function relativeTime(date: string, locale: string): string {
  const diff = Date.now() - new Date(date).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return locale === "ko" ? "방금 전" : "just now";
  if (hours < 24) return locale === "ko" ? `${hours}시간 전` : `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return locale === "ko" ? `${days}일 전` : `${days}d ago`;
  return locale === "ko" ? `${Math.floor(days / 7)}주 전` : `${Math.floor(days / 7)}w ago`;
}

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
  }, [world?.id, fetchFeed, fetchConversations]);

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
        <span className="font-sans text-base text-hud-muted">
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
        if (item.type === "post") {
          return (
            <PostCard
              key={`post-${item.data.id || i}`}
              data={item.data}
              createdAt={item.created_at}
              locale={locale}
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
  const firstSpeaker = names[0] || "";

  return (
    <button
      onClick={onClick}
      className="w-full text-left p-4 border border-hud-border hover:border-accent/40 hover:bg-accent/5 transition-colors rounded"
    >
      {/* Topic */}
      <h4 className="font-sans text-base font-semibold text-hud-text leading-snug mb-1">
        {topic}
      </h4>

      {/* First speaker • relative time */}
      <div className="font-sans text-sm text-hud-muted mb-2">
        {firstSpeaker}
        {createdAt && (
          <span className="text-hud-label"> • {relativeTime(createdAt, locale)}</span>
        )}
      </div>

      {/* Preview */}
      {preview && (
        <p className="font-sans text-sm text-hud-muted line-clamp-2 leading-relaxed mb-3">
          {preview}
        </p>
      )}

      {/* Bottom row: avatars + message count */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1">
          {names.slice(0, 3).map((name, i) => (
            <AgentAvatar key={i} name={name} size="sm" />
          ))}
          {names.length > 3 && (
            <span className="font-mono text-sm text-hud-muted ml-1">
              +{names.length - 3}
            </span>
          )}
        </div>
        <span className="font-mono text-sm text-hud-muted">
          💬 {msgCount}
        </span>
      </div>
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
        <span className="font-mono text-base text-success uppercase">WIKI</span>
        <span className="font-sans text-base text-hud-text flex-1 truncate">
          {agentName ? `${agentName} updated ` : ""}<span className="font-semibold text-hud-text">{title}</span>
        </span>
        <span
          className={`font-mono text-base px-1.5 py-0.5 border rounded uppercase ${statusColor[status] || "text-hud-muted border-hud-border"}`}
        >
          {status}
        </span>
      </div>
      {createdAt && (
        <div className="font-mono text-base text-hud-label mt-1">
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
          <span className="text-hud-muted ml-2 normal-case text-base">
            {themeCount} themes
          </span>
        )}
      </span>
    </div>
  );
}

function PostCard({
  data,
  createdAt,
  locale,
  t,
}: {
  data: Record<string, unknown>;
  createdAt: string | null;
  locale: string;
  t: (en: string, ko?: string | null) => string;
}) {
  const agentName = data.agent_name as string;
  const rawTitle = data.title as string | null;
  const title = rawTitle ? t(rawTitle, data.title_ko as string | undefined) : null;
  const content = t(data.content as string, data.content_ko as string | undefined);

  return (
    <div className="w-full p-4 border border-hud-border rounded bg-surface/50">
      {/* Header: Avatar + Name + Time */}
      <div className="flex items-center gap-3 mb-3">
        <AgentAvatar name={agentName} size="md" />
        <div className="flex-1 min-w-0">
          <span className="font-sans text-base font-semibold text-hud-text">
            {agentName}
          </span>
          {createdAt && (
            <span className="font-sans text-sm text-hud-muted ml-2">
              {relativeTime(createdAt, locale)}
            </span>
          )}
        </div>
      </div>

      {/* Title (if present) */}
      {title && (
        <h4 className="font-sans text-base font-semibold text-hud-text mb-2">
          {title}
        </h4>
      )}

      {/* Content */}
      <p className="font-sans text-sm text-hud-text leading-relaxed whitespace-pre-wrap">
        {content}
      </p>
    </div>
  );
}

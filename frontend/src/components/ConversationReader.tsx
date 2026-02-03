"use client";

import { useLocale } from "next-intl";
import { useSimulationStore } from "@/stores/simulation";
import { AgentAvatar } from "./AgentAvatar";

export function ConversationReader() {
  const locale = useLocale();
  const { conversations, selectedConversation, setSelectedConversation } =
    useSimulationStore();

  const t = (en: string, ko?: string | null) =>
    locale === "ko" && ko ? ko : en;

  const conv = conversations.find((c) => c.id === selectedConversation);

  if (!conv) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-sans text-base text-hud-muted">
          Select a conversation to read
        </span>
      </div>
    );
  }

  const displayTopic = t(conv.topic, conv.topic_ko);
  const displaySummary = t(conv.summary, conv.summary_ko);
  const messages = conv.messages || [];
  const messagesKo = conv.messages_ko || [];

  // Build participant lookup
  const participantMap = new Map(
    conv.participants.map((p) => [p.id, p])
  );

  // Find prev/next conversation
  const idx = conversations.findIndex((c) => c.id === conv.id);
  const prevConv = idx < conversations.length - 1 ? conversations[idx + 1] : null;
  const nextConv = idx > 0 ? conversations[idx - 1] : null;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-hud-border space-y-2">
        <button
          onClick={() => setSelectedConversation(null)}
          className="label-text text-accent hover:text-accent/80"
        >
          ← BACK TO FEED
        </button>
        <h2 className="font-sans text-lg font-semibold text-hud-text leading-snug">
          {displayTopic}
        </h2>
        <div className="flex items-center gap-3">
          <span className="font-mono text-sm text-accent uppercase">
            Epoch {conv.epoch}
          </span>
          <span className="font-mono text-sm text-hud-muted">
            {conv.participants.length} participants
          </span>
        </div>
        <div className="flex items-center gap-1">
          {conv.participants.map((p) => (
            <AgentAvatar
              key={p.id}
              name={p.name}
              factionColor={p.faction_color}
              size="sm"
            />
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => {
          const agentId = msg.agent_id as string;
          const agentName =
            (msg.agent_name as string) ||
            participantMap.get(agentId)?.name ||
            "Unknown";
          const participant = participantMap.get(agentId);
          const color = participant?.faction_color || "#6366f1";

          const koMsg = messagesKo[i];
          const content = koMsg
            ? t(msg.content as string, koMsg.content as string)
            : (msg.content as string);

          return (
            <div key={i} className="flex gap-3">
              <AgentAvatar
                name={agentName}
                factionColor={color}
                size="md"
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className="font-sans text-base font-semibold"
                    style={{ color }}
                  >
                    {agentName}
                  </span>
                  {participant && (
                    <span className="font-mono text-base text-hud-muted">
                      {/* Faction name could be derived but we have color */}
                    </span>
                  )}
                </div>
                <div
                  className="font-sans text-base text-hud-text leading-relaxed pl-3"
                  style={{ borderLeft: `3px solid ${color}40` }}
                >
                  {content}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer: Summary + Navigation */}
      <div className="border-t border-hud-border p-4 space-y-3">
        {displaySummary && (
          <details className="group">
            <summary className="label-text cursor-pointer select-none">
              SUMMARY
            </summary>
            <p className="font-sans text-base text-hud-muted mt-2 leading-relaxed">
              {displaySummary}
            </p>
          </details>
        )}
        <div className="flex items-center justify-between">
          <button
            onClick={() => prevConv && setSelectedConversation(prevConv.id)}
            disabled={!prevConv}
            className="font-mono text-sm text-accent hover:text-accent/80 disabled:text-hud-label disabled:cursor-not-allowed uppercase"
          >
            ← Prev
          </button>
          <button
            onClick={() => nextConv && setSelectedConversation(nextConv.id)}
            disabled={!nextConv}
            className="font-mono text-sm text-accent hover:text-accent/80 disabled:text-hud-label disabled:cursor-not-allowed uppercase"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}

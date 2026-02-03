"use client";

import { WorldData } from "@/stores/simulation";

interface WorldCardProps {
  world: WorldData;
  locale: string;
}

export function WorldCard({ world, locale }: WorldCardProps) {
  const tags = world.tags || [];
  const description =
    (world.config as Record<string, unknown>)?.description as string || "";

  return (
    <a
      href={`/${locale}/world/${world.id}`}
      className="block p-4 rounded-lg border border-hud-border bg-void-light/30 hover:border-accent/50 hover:bg-void-light/60 transition-all group"
    >
      <p className="text-sm text-hud-text group-hover:text-accent font-medium truncate mb-2">
        {world.seed_prompt}
      </p>

      {description && (
        <p className="text-sm font-sans text-hud-muted line-clamp-2 mb-3">
          {description}
        </p>
      )}

      {world.latest_activity && (
        <p className="font-sans text-xs text-hud-muted italic truncate mb-2">
          {world.latest_activity}
        </p>
      )}

      <div className="flex items-center gap-3 mb-2">
        <Stat label="EPOCHS" value={world.epoch_count ?? world.current_epoch} />
        <Stat label="WIKI" value={world.wiki_page_count ?? 0} />
        <Stat label="AGENTS" value={world.agent_count ?? 0} />
        <Stat label="CONVOS" value={world.conversation_count ?? 0} />
      </div>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {tags.slice(0, 5).map((t) => (
            <span
              key={t.tag}
              className="px-1.5 py-0.5 text-xs font-mono uppercase tracking-wider text-hud-muted border border-hud-border rounded"
            >
              {t.tag}
            </span>
          ))}
        </div>
      )}
    </a>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center gap-1">
      <span className="font-mono text-xs text-accent">{value}</span>
      <span className="font-mono text-xs text-hud-label uppercase">{label}</span>
    </div>
  );
}

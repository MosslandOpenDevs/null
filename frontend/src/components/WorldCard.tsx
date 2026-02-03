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
      className="block p-4 rounded-lg border border-gray-800 bg-void-light/30 hover:border-accent/50 hover:bg-void-light/60 transition-all group"
    >
      <p className="text-sm text-gray-200 group-hover:text-white font-medium truncate mb-2">
        {world.seed_prompt}
      </p>

      {description && (
        <p className="text-sm font-sans text-gray-500 line-clamp-2 mb-3">
          {description}
        </p>
      )}

      {world.latest_activity && (
        <p className="font-sans text-xs text-gray-400 italic truncate mb-2">
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
              className="px-1.5 py-0.5 text-xs font-mono uppercase tracking-wider text-gray-500 border border-gray-700 rounded"
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
      <span className="font-mono text-xs text-gray-600 uppercase">{label}</span>
    </div>
  );
}

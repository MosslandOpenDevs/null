import { create } from "zustand";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

export interface WorldData {
  id: string;
  seed_prompt: string;
  config: Record<string, unknown>;
  status: string;
  current_epoch: number;
  current_tick: number;
  agent_count?: number;
  conversation_count?: number;
  wiki_page_count?: number;
  epoch_count?: number;
  latest_activity?: string | null;
  tags?: Array<{ tag: string; weight: number }>;
}

export interface AgentData {
  id: string;
  world_id: string;
  faction_id: string | null;
  name: string;
  persona: Record<string, unknown>;
  beliefs: unknown[];
  status: string;
}

export interface FactionData {
  id: string;
  world_id: string;
  name: string;
  description: string;
  color: string;
  agent_count: number;
}

export interface RelationshipData {
  id: string;
  agent_a: string;
  agent_b: string;
  type: string;
  strength: number;
}

export interface WikiPageData {
  id: string;
  world_id: string;
  title: string;
  content: string;
  title_ko?: string | null;
  content_ko?: string | null;
  status: string;
  version: number;
  created_at: string;
}


export interface WSEvent {
  type: string;
  timestamp: string;
  epoch: number;
  payload: Record<string, unknown>;
}

export interface ConversationData {
  id: string;
  epoch: number;
  tick: number;
  topic: string;
  topic_ko?: string | null;
  participants: Array<{ id: string; name: string; faction_color: string }>;
  messages: Array<Record<string, unknown>>;
  messages_ko?: Array<Record<string, unknown>> | null;
  summary: string;
  summary_ko?: string | null;
  created_at: string;
}

export type FeedItem = {
  type: "conversation" | "wiki_edit" | "epoch" | "post";
  data: Record<string, unknown>;
  created_at: string | null;
};

interface SimulationState {
  world: WorldData | null;
  agents: AgentData[];
  factions: FactionData[];
  relationships: RelationshipData[];
  wikiPages: WikiPageData[];
  events: WSEvent[];
  selectedAgent: string | null;
  selectedFaction: string | null;
  intelTab: "agent" | "wiki" | "log" | "resonance" | "strata" | "ops" | "export" | "feed";
  heraldMessages: Array<{ id: string; text: string; timestamp: number }>;
  conversations: ConversationData[];
  feedItems: FeedItem[];
  selectedConversation: string | null;
  autoWorlds: WorldData[];
  worldTags: Record<string, Array<{ tag: string; weight: number }>>;
  tagFilter: string | null;

  createWorld: (seedPrompt: string) => Promise<void>;
  fetchWorld: (id: string) => Promise<void>;
  fetchAgents: (worldId: string) => Promise<void>;
  fetchFactions: (worldId: string) => Promise<void>;
  fetchRelationships: (worldId: string) => Promise<void>;
  fetchWikiPages: (worldId: string) => Promise<void>;
  fetchAutoWorlds: () => Promise<void>;
  startSimulation: (worldId: string) => Promise<void>;
  stopSimulation: (worldId: string) => Promise<void>;
  addEvent: (event: WSEvent) => void;
  setSelectedAgent: (id: string | null) => void;
  setSelectedFaction: (id: string | null) => void;
  fetchConversations: (worldId: string) => Promise<void>;
  fetchFeed: (worldId: string, before?: string) => Promise<void>;
  setSelectedConversation: (id: string | null) => void;
  setIntelTab: (tab: "agent" | "wiki" | "log" | "resonance" | "strata" | "ops" | "export" | "feed") => void;
  addHeraldMessage: (text: string) => void;
  dismissHerald: (id: string) => void;
  setTagFilter: (tag: string | null) => void;
  exportWorld: (worldId: string, type: string, format: string) => Promise<void>;
}

export const useSimulationStore = create<SimulationState>((set, get) => ({
  world: null,
  agents: [],
  factions: [],
  relationships: [],
  wikiPages: [],
  events: [],
  selectedAgent: null,
  selectedFaction: null,
  intelTab: "feed",
  heraldMessages: [],
  conversations: [],
  feedItems: [],
  selectedConversation: null,
  autoWorlds: [],
  worldTags: {},
  tagFilter: null,

  createWorld: async (seedPrompt: string) => {
    const resp = await fetch(`${API_URL}/api/worlds`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed_prompt: seedPrompt }),
    });
    const world = await resp.json();
    // No redirect — stay on home page, world appears in Incubator
    // Refresh the world list so the new world shows up
    get().fetchAutoWorlds();
  },

  fetchWorld: async (id: string) => {
    const resp = await fetch(`${API_URL}/api/worlds/${id}`);
    const world = await resp.json();
    set({ world });
    get().fetchAgents(id);
    get().fetchFactions(id);
    get().fetchRelationships(id);
    get().fetchWikiPages(id);
  },

  fetchAgents: async (worldId: string) => {
    const resp = await fetch(`${API_URL}/api/worlds/${worldId}/agents`);
    const agents = await resp.json();
    set({ agents });
  },

  fetchFactions: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/factions`);
      if (resp.ok) {
        const factions = await resp.json();
        set({ factions });
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  fetchRelationships: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/relationships`);
      if (resp.ok) {
        const relationships = await resp.json();
        set({ relationships });
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  fetchWikiPages: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/wiki`);
      if (resp.ok) {
        const wikiPages = await resp.json();
        set({ wikiPages });
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  fetchAutoWorlds: async () => {
    try {
      const tagFilter = get().tagFilter;
      const url = tagFilter
        ? `${API_URL}/api/worlds?tag=${encodeURIComponent(tagFilter)}`
        : `${API_URL}/api/worlds`;
      const resp = await fetch(url);
      if (resp.ok) {
        const worlds = await resp.json();
        // Extract tags from response
        const worldTags: Record<string, Array<{ tag: string; weight: number }>> = {};
        for (const w of worlds) {
          if (w.tags) {
            worldTags[w.id] = w.tags;
          }
        }
        set({ autoWorlds: worlds, worldTags });
      }
    } catch {
      // backend may not be ready yet
    }
  },

  startSimulation: async (worldId: string) => {
    await fetch(`${API_URL}/api/worlds/${worldId}/start`, { method: "POST" });
    set((s) => ({ world: s.world ? { ...s.world, status: "running" } : null }));
  },

  stopSimulation: async (worldId: string) => {
    await fetch(`${API_URL}/api/worlds/${worldId}/stop`, { method: "POST" });
    set((s) => ({ world: s.world ? { ...s.world, status: "paused" } : null }));
  },

  addEvent: (event: WSEvent) => {
    set((s) => ({
      events: [...s.events.slice(-500), event],
      world: s.world
        ? {
            ...s.world,
            current_epoch: event.epoch,
            current_tick: event.payload.tick != null
              ? (event.payload.tick as number)
              : s.world.current_tick,
          }
        : null,
    }));

    if (event.type === "herald.announcement") {
      get().addHeraldMessage(event.payload.text as string);
    }

    // Refresh data on key events
    const world = get().world;
    if (world && (event.type === "wiki.edit" || event.type === "epoch.transition")) {
      get().fetchWikiPages(world.id);
    }
    if (world && event.type === "relation.update") {
      get().fetchRelationships(world.id);
    }
  },

  fetchConversations: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/conversations?limit=50`);
      if (resp.ok) {
        const conversations = await resp.json();
        set({ conversations });
      }
    } catch {
      // endpoint may not be ready
    }
  },

  fetchFeed: async (worldId: string, before?: string) => {
    try {
      const url = before
        ? `${API_URL}/api/worlds/${worldId}/feed?limit=20&before=${encodeURIComponent(before)}`
        : `${API_URL}/api/worlds/${worldId}/feed?limit=20`;
      const resp = await fetch(url);
      if (resp.ok) {
        const items = await resp.json();
        if (before) {
          set((s) => ({ feedItems: [...s.feedItems, ...items] }));
        } else {
          set({ feedItems: items });
        }
      }
    } catch {
      // endpoint may not be ready
    }
  },

  setSelectedConversation: (id) => set({ selectedConversation: id }),

  setSelectedAgent: (id) => set({ selectedAgent: id, intelTab: "agent" }),
  setSelectedFaction: (id) => set({ selectedFaction: id }),
  setIntelTab: (tab) => set({ intelTab: tab }),
  setTagFilter: (tag) => {
    set({ tagFilter: tag });
    get().fetchAutoWorlds();
  },

  exportWorld: async (worldId: string, type: string, format: string) => {
    const url = `${API_URL}/api/worlds/${worldId}/export/${type}?format=${format}`;
    const resp = await fetch(url);
    const blob = await resp.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${type}.${format === "jsonl" ? "jsonl" : format === "csv" ? "csv" : format === "md" ? "md" : "json"}`;
    a.click();
    URL.revokeObjectURL(a.href);
  },

  addHeraldMessage: (text: string) => {
    const id = Math.random().toString(36).slice(2);
    set((s) => ({
      heraldMessages: [...s.heraldMessages, { id, text, timestamp: Date.now() }],
    }));
    setTimeout(() => get().dismissHerald(id), 8000);
  },

  dismissHerald: (id: string) => {
    set((s) => ({
      heraldMessages: s.heraldMessages.filter((m) => m.id !== id),
    }));
  },
}));

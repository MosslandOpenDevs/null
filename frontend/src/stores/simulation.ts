import { create } from "zustand";
import type { ChronicleItem } from "@/components/chronicle/types";

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

export interface FocusFilter {
  type: "all" | "agent" | "faction";
  id?: string;
}

export interface OracleTarget {
  type: "agent" | "wiki" | "faction" | "event";
  id: string;
}

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

  // Chronicle state
  chronicleItems: ChronicleItem[];
  focusFilter: FocusFilter;
  activeAgentIds: Set<string>;

  // Oracle panel state
  oracleTarget: OracleTarget | null;
  oracleOpen: boolean;

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
  setFocusFilter: (filter: FocusFilter) => void;
  openOracle: (target: OracleTarget) => void;
  closeOracle: () => void;
  addChronicleItem: (item: ChronicleItem) => void;
  loadChronicleFromDB: (worldId: string) => Promise<void>;
}

function classifyEventType(payload: Record<string, unknown>): "crisis" | "discovery" | "plague" | "leadership" | "general" {
  const desc = ((payload.description as string) || (payload.text as string) || "").toLowerCase();
  if (desc.includes("crisis") || desc.includes("conflict") || desc.includes("war")) return "crisis";
  if (desc.includes("discover") || desc.includes("found") || desc.includes("breakthrough")) return "discovery";
  if (desc.includes("plague") || desc.includes("disease") || desc.includes("death")) return "plague";
  if (desc.includes("leader") || desc.includes("elect") || desc.includes("crown")) return "leadership";
  return "general";
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
  chronicleItems: [],
  focusFilter: { type: "all" },
  activeAgentIds: new Set<string>(),
  oracleTarget: null,
  oracleOpen: false,

  createWorld: async (seedPrompt: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seed_prompt: seedPrompt }),
      });
      if (!resp.ok) console.error("[Store] createWorld failed:", resp.status);
      get().fetchAutoWorlds();
    } catch (err) {
      console.error("[Store] createWorld error:", err);
    }
  },

  fetchWorld: async (id: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${id}`);
      if (!resp.ok) {
        console.error("[Store] fetchWorld failed:", resp.status);
        return;
      }
      const world = await resp.json();
      set({ world });
      get().fetchAgents(id);
      get().fetchFactions(id);
      get().fetchRelationships(id);
      get().fetchWikiPages(id);
      await get().loadChronicleFromDB(id);
    } catch (err) {
      console.error("[Store] fetchWorld error:", err);
    }
  },

  fetchAgents: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/agents`);
      if (resp.ok) {
        const agents = await resp.json();
        set({ agents });
      } else {
        console.warn("[Store] fetchAgents:", resp.status);
      }
    } catch (err) {
      console.error("[Store] fetchAgents error:", err);
    }
  },

  fetchFactions: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/factions`);
      if (resp.ok) {
        const factions = await resp.json();
        set({ factions });
      }
    } catch (err) {
      console.warn("[Store] fetchFactions:", err);
    }
  },

  fetchRelationships: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/relationships`);
      if (resp.ok) {
        const relationships = await resp.json();
        set({ relationships });
      }
    } catch (err) {
      console.warn("[Store] fetchRelationships:", err);
    }
  },

  fetchWikiPages: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/wiki`);
      if (resp.ok) {
        const wikiPages = await resp.json();
        set({ wikiPages });
      }
    } catch (err) {
      console.warn("[Store] fetchWikiPages:", err);
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
        const worldTags: Record<string, Array<{ tag: string; weight: number }>> = {};
        for (const w of worlds) {
          if (w.tags) {
            worldTags[w.id] = w.tags;
          }
        }
        set({ autoWorlds: worlds, worldTags });
      } else {
        console.warn("[Store] fetchAutoWorlds:", resp.status);
      }
    } catch (err) {
      console.warn("[Store] fetchAutoWorlds:", err);
    }
  },

  startSimulation: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/start`, { method: "POST" });
      if (!resp.ok) console.error("[Store] startSimulation failed:", resp.status);
      set((s) => ({ world: s.world ? { ...s.world, status: "running" } : null }));
    } catch (err) {
      console.error("[Store] startSimulation error:", err);
    }
  },

  stopSimulation: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/stop`, { method: "POST" });
      if (!resp.ok) console.error("[Store] stopSimulation failed:", resp.status);
      set((s) => ({ world: s.world ? { ...s.world, status: "paused" } : null }));
    } catch (err) {
      console.error("[Store] stopSimulation error:", err);
    }
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

    // Route events to Chronicle
    const ts = event.timestamp;
    const epoch = event.epoch;
    const tick = (event.payload.tick as number) ?? 0;

    if (event.type === "herald.announcement") {
      get().addHeraldMessage(event.payload.text as string);
      get().addChronicleItem({
        type: "herald",
        id: `herald-${ts}`,
        epoch,
        tick,
        timestamp: ts,
        text: event.payload.text as string,
      });
    }

    if (event.type === "agent.message") {
      const agentId = event.payload.agent_id as string;
      // Track active agent
      set((s) => {
        const newActive = new Set(s.activeAgentIds);
        newActive.add(agentId);
        return { activeAgentIds: newActive };
      });
      // Clear active status after 10s
      setTimeout(() => {
        set((s) => {
          const newActive = new Set(s.activeAgentIds);
          newActive.delete(agentId);
          return { activeAgentIds: newActive };
        });
      }, 10000);

      // Build conversation block from accumulated messages
      const convId = (event.payload.conversation_id as string) || `conv-${epoch}-${tick}`;
      const agents = get().agents;
      const factions = get().factions;
      const factionMap = new Map(factions.map((f) => [f.id, f]));
      const agent = agents.find((a) => a.id === agentId);
      const faction = agent?.faction_id ? factionMap.get(agent.faction_id) : null;

      set((s) => {
        const existingIdx = s.chronicleItems.findIndex(
          (item) => item.type === "conversation" && item.id === convId
        );

        const newMsg = {
          agent_id: agentId,
          agent_name: agent?.name || (event.payload.agent_name as string) || "Unknown",
          content: event.payload.content as string,
          faction_color: faction?.color || "#6366f1",
        };

        if (existingIdx >= 0) {
          const existing = s.chronicleItems[existingIdx];
          if (existing.type === "conversation") {
            const updated = {
              ...existing,
              messages: [...existing.messages, newMsg],
            };
            const items = [...s.chronicleItems];
            items[existingIdx] = updated;
            return { chronicleItems: items };
          }
        }

        // Create new conversation block
        const newConv: ChronicleItem = {
          type: "conversation",
          id: convId,
          epoch,
          tick,
          timestamp: ts,
          topic: (event.payload.topic as string) || "Discussion",
          participants: [
            {
              id: agentId,
              name: agent?.name || "Unknown",
              faction_id: agent?.faction_id || null,
              faction_color: faction?.color || "#6366f1",
            },
          ],
          messages: [newMsg],
        };

        return { chronicleItems: [newConv, ...s.chronicleItems].slice(0, 500) };
      });
    }

    if (event.type === "event.triggered") {
      get().addChronicleItem({
        type: "event",
        id: `event-${ts}`,
        epoch,
        tick,
        timestamp: ts,
        eventType: classifyEventType(event.payload),
        description: (event.payload.description as string) || (event.payload.text as string) || "Event occurred",
        affectedAgents: event.payload.affected_agents as string[] | undefined,
      });
    }

    if (event.type === "wiki.edit" || event.type === "wiki.created") {
      get().addChronicleItem({
        type: "wiki",
        id: `wiki-${ts}-${event.payload.page_id || "new"}`,
        epoch,
        tick,
        timestamp: ts,
        title: (event.payload.title as string) || "New Knowledge",
        content: (event.payload.content as string) || (event.payload.summary as string) || "",
        version: (event.payload.version as number) || 1,
      });
      const world = get().world;
      if (world) get().fetchWikiPages(world.id);
    }

    if (event.type === "epoch.transition" || event.type === "epoch.end") {
      get().addChronicleItem({
        type: "epoch",
        id: `epoch-${epoch}`,
        epoch,
        timestamp: ts,
        summary: event.payload.summary as string | undefined,
        dominantTheme: event.payload.dominant_theme as "prosperity" | "conflict" | "discovery" | "transition" | undefined,
      });
    }

    if (event.type === "relation.update") {
      const world = get().world;
      if (world) get().fetchRelationships(world.id);
    }
  },

  fetchConversations: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/conversations?limit=50`);
      if (resp.ok) {
        const conversations = await resp.json();
        set({ conversations });
      }
    } catch (err) {
      console.warn("[Store] fetchConversations:", err);
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
    } catch (err) {
      console.warn("[Store] fetchFeed:", err);
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
    try {
      const url = `${API_URL}/api/worlds/${worldId}/export/${type}?format=${format}`;
      const resp = await fetch(url);
      if (!resp.ok) {
        console.error("[Store] exportWorld failed:", resp.status);
        return;
      }
      const blob = await resp.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${type}.${format === "jsonl" ? "jsonl" : format === "csv" ? "csv" : format === "md" ? "md" : "json"}`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      console.error("[Store] exportWorld error:", err);
    }
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

  setFocusFilter: (filter: FocusFilter) => set({ focusFilter: filter }),

  openOracle: (target: OracleTarget) =>
    set({ oracleTarget: target, oracleOpen: true }),

  closeOracle: () =>
    set({ oracleOpen: false }),

  addChronicleItem: (item: ChronicleItem) => {
    set((s) => ({
      chronicleItems: [item, ...s.chronicleItems].slice(0, 500),
    }));
  },

  loadChronicleFromDB: async (worldId: string) => {
    try {
      // Fetch conversations and wiki pages in parallel
      const [convResp, wikiResp] = await Promise.all([
        fetch(`${API_URL}/api/worlds/${worldId}/conversations?limit=50`),
        fetch(`${API_URL}/api/worlds/${worldId}/wiki`),
      ]);

      const items: ChronicleItem[] = [];

      if (convResp.ok) {
        const conversations: ConversationData[] = await convResp.json();
        for (const conv of conversations) {
          items.push({
            type: "conversation",
            id: conv.id,
            epoch: conv.epoch,
            tick: conv.tick,
            timestamp: conv.created_at,
            topic: conv.topic_ko || conv.topic,
            participants: conv.participants.map((p) => ({
              id: p.id,
              name: p.name,
              faction_id: null,
              faction_color: p.faction_color || "#6366f1",
            })),
            messages: (conv.messages_ko || conv.messages).map((m) => ({
              agent_id: (m.agent_id as string) || "",
              agent_name:
                conv.participants.find((p) => p.id === m.agent_id)?.name || "Unknown",
              content: (m.content as string) || "",
              faction_color:
                conv.participants.find((p) => p.id === m.agent_id)?.faction_color || "#6366f1",
            })),
          });
        }
      }

      if (wikiResp.ok) {
        const wikiPages: WikiPageData[] = await wikiResp.json();
        for (const page of wikiPages) {
          items.push({
            type: "wiki",
            id: `wiki-${page.id}`,
            epoch: 0,
            tick: 0,
            timestamp: page.created_at,
            title: page.title_ko || page.title,
            content: (page.content_ko || page.content).slice(0, 300),
            version: page.version,
          });
        }
      }

      // Merge with any existing WS items (avoid duplicates)
      const existing = get().chronicleItems;
      const existingIds = new Set(existing.map((i) => i.id));
      const merged = [...existing];
      for (const item of items) {
        if (!existingIds.has(item.id)) {
          merged.push(item);
        }
      }

      // Sort by timestamp descending (newest first)
      merged.sort((a, b) => {
        const ta = a.timestamp || "";
        const tb = b.timestamp || "";
        return tb.localeCompare(ta);
      });

      console.log("[Chronicle] Loaded from DB:", items.length, "items, merged total:", merged.length);
      set({ chronicleItems: merged.slice(0, 500) });
    } catch (err) {
      console.error("[Chronicle] loadChronicleFromDB failed:", err);
    }
  },
}));

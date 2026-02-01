import { create } from "zustand";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

export interface ClusterData {
  id: string;
  label: string;
  description: string;
  member_count: number;
  created_at: string;
}

export interface ClusterMember {
  id: string;
  cluster_id: string;
  world_id: string;
  entity_type: string;
  entity_id: string;
  similarity: number;
}

export interface ResonanceLink {
  id: string;
  cluster_id: string | null;
  world_a: string;
  world_b: string;
  entity_a: string;
  entity_b: string;
  entity_type: string;
  strength: number;
}

export interface GlobalSearchResult {
  entity_type: string;
  entity_id: string;
  world_id: string;
  title: string;
  snippet: string;
  score: number;
}

interface MultiverseState {
  clusters: ClusterData[];
  resonanceLinks: ResonanceLink[];
  searchResults: GlobalSearchResult[];
  searching: boolean;

  fetchClusters: () => Promise<void>;
  fetchResonance: (worldId: string) => Promise<void>;
  globalSearch: (query: string) => Promise<void>;
}

export const useMultiverseStore = create<MultiverseState>((set) => ({
  clusters: [],
  resonanceLinks: [],
  searchResults: [],
  searching: false,

  fetchClusters: async () => {
    try {
      const resp = await fetch(`${API_URL}/api/multiverse/clusters`);
      if (resp.ok) {
        const clusters = await resp.json();
        set({ clusters });
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  fetchResonance: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/multiverse/resonance?world_id=${worldId}`);
      if (resp.ok) {
        const resonanceLinks = await resp.json();
        set({ resonanceLinks });
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  globalSearch: async (query: string) => {
    set({ searching: true });
    try {
      const resp = await fetch(
        `${API_URL}/api/multiverse/search?q=${encodeURIComponent(query)}`
      );
      if (resp.ok) {
        const searchResults = await resp.json();
        set({ searchResults });
      }
    } catch {
      // endpoint may not exist yet
    } finally {
      set({ searching: false });
    }
  },
}));

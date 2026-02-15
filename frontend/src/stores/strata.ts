import { create } from "zustand";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

export interface StratumData {
  id: string;
  world_id: string;
  epoch: number;
  summary: string;
  summary_ko?: string | null;
  emerged_concepts: string[];
  faded_concepts: string[];
  dominant_themes: string[];
}

export interface StrataComparisonData {
  world_id: string;
  from_epoch: number;
  to_epoch: number;
  from_summary: string;
  from_summary_ko?: string | null;
  to_summary: string;
  to_summary_ko?: string | null;
  added_themes: string[];
  removed_themes: string[];
  persisted_themes: string[];
  newly_emerged_concepts: string[];
  newly_faded_concepts: string[];
}

interface StrataState {
  strata: StratumData[];
  comparison: StrataComparisonData | null;
  comparisonLoading: boolean;

  fetchStrata: (worldId: string) => Promise<void>;
  fetchComparison: (worldId: string, fromEpoch: number, toEpoch: number) => Promise<void>;
  clearComparison: () => void;
}

export const useStrataStore = create<StrataState>((set) => ({
  strata: [],
  comparison: null,
  comparisonLoading: false,

  fetchStrata: async (worldId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/worlds/${worldId}/strata`);
      if (resp.ok) {
        const strata = await resp.json();
        set({ strata });
      }
    } catch {
      set({ strata: [] });
    }
  },

  fetchComparison: async (worldId: string, fromEpoch: number, toEpoch: number) => {
    set({ comparisonLoading: true });
    try {
      const resp = await fetch(
        `${API_URL}/api/worlds/${worldId}/strata/compare?from_epoch=${fromEpoch}&to_epoch=${toEpoch}`
      );
      if (resp.ok) {
        const comparison = await resp.json();
        set({ comparison });
      } else {
        set({ comparison: null });
      }
    } catch {
      set({ comparison: null });
    } finally {
      set({ comparisonLoading: false });
    }
  },

  clearComparison: () => set({ comparison: null }),
}));

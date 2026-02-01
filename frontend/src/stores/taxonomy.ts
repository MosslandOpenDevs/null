import { create } from "zustand";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

export interface TaxonomyNode {
  id: string;
  parent_id: string | null;
  label: string;
  description: string;
  depth: number;
  path: string;
  member_count: number;
}

export interface TaxonomyMembership {
  id: string;
  node_id: string;
  world_id: string;
  entity_type: string;
  entity_id: string;
  similarity: number;
}

export interface TaxonomyNodeDetail {
  node: TaxonomyNode;
  children: TaxonomyNode[];
  members: TaxonomyMembership[];
}

interface TaxonomyState {
  rootNodes: TaxonomyNode[];
  selectedNode: TaxonomyNodeDetail | null;
  selectedNodeId: string | null;

  fetchTree: () => Promise<void>;
  fetchNode: (nodeId: string) => Promise<void>;
  setSelectedNodeId: (id: string | null) => void;
}

export const useTaxonomyStore = create<TaxonomyState>((set) => ({
  rootNodes: [],
  selectedNode: null,
  selectedNodeId: null,

  fetchTree: async () => {
    try {
      const resp = await fetch(`${API_URL}/api/taxonomy/tree`);
      if (resp.ok) {
        const rootNodes = await resp.json();
        set({ rootNodes });
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  fetchNode: async (nodeId: string) => {
    try {
      const resp = await fetch(`${API_URL}/api/taxonomy/tree/${nodeId}`);
      if (resp.ok) {
        const selectedNode = await resp.json();
        set({ selectedNode, selectedNodeId: nodeId });
      }
    } catch {
      // endpoint may not exist yet
    }
  },

  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
}));

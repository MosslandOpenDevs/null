import assert from "node:assert/strict";
import test from "node:test";

import { useTaxonomyStore } from "../src/stores/taxonomy.ts";

function resetTaxonomyStore() {
  useTaxonomyStore.setState({
    rootNodes: [],
    selectedNode: null,
    selectedNodeId: null,
  });
}

test("setSelectedNodeId updates selected id", () => {
  resetTaxonomyStore();
  useTaxonomyStore.getState().setSelectedNodeId("node-1");
  assert.equal(useTaxonomyStore.getState().selectedNodeId, "node-1");
});

test("fetchTree loads root nodes when api returns ok", async () => {
  resetTaxonomyStore();
  const originalFetch = global.fetch;
  global.fetch = (async () => ({
    ok: true,
    json: async () => [
      {
        id: "root-1",
        parent_id: null,
        label: "root",
        description: "root node",
        depth: 0,
        path: "/root",
        member_count: 2,
      },
    ],
  })) as unknown as typeof fetch;

  try {
    await useTaxonomyStore.getState().fetchTree();
  } finally {
    global.fetch = originalFetch;
  }

  assert.equal(useTaxonomyStore.getState().rootNodes.length, 1);
  assert.equal(useTaxonomyStore.getState().rootNodes[0].id, "root-1");
});

test("fetchNode loads selected node detail and selected id", async () => {
  resetTaxonomyStore();
  const originalFetch = global.fetch;
  global.fetch = (async () => ({
    ok: true,
    json: async () => ({
      node: {
        id: "n-10",
        parent_id: null,
        label: "economy",
        description: "economy concepts",
        depth: 1,
        path: "/economy",
        member_count: 3,
      },
      children: [],
      members: [],
    }),
  })) as unknown as typeof fetch;

  try {
    await useTaxonomyStore.getState().fetchNode("n-10");
  } finally {
    global.fetch = originalFetch;
  }

  const state = useTaxonomyStore.getState();
  assert.equal(state.selectedNodeId, "n-10");
  assert.equal(state.selectedNode?.node.label, "economy");
});

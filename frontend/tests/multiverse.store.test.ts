import assert from "node:assert/strict";
import test from "node:test";

import { useMultiverseStore } from "../src/stores/multiverse.ts";

function resetMultiverseStore() {
  useMultiverseStore.setState({
    clusters: [],
    resonanceLinks: [],
    worldNeighbors: [],
    worldsMap: null,
    searchResults: [],
    searching: false,
  });
}

test("fetchWorldNeighbors loads neighbor rankings", async () => {
  resetMultiverseStore();
  const originalFetch = global.fetch;
  global.fetch = (async () => ({
    ok: true,
    json: async () => [
      {
        world_id: "w-2",
        seed_prompt: "Neighbor World",
        status: "running",
        strength: 0.81,
        resonance_count: 7,
      },
    ],
  })) as unknown as typeof fetch;

  try {
    await useMultiverseStore.getState().fetchWorldNeighbors("w-1", 0.3);
  } finally {
    global.fetch = originalFetch;
  }

  const state = useMultiverseStore.getState();
  assert.equal(state.worldNeighbors.length, 1);
  assert.equal(state.worldNeighbors[0].world_id, "w-2");
  assert.equal(state.worldNeighbors[0].resonance_count, 7);
});

test("fetchWorldMap loads deduplicated world map payload", async () => {
  resetMultiverseStore();
  const originalFetch = global.fetch;
  global.fetch = (async () => ({
    ok: true,
    json: async () => ({
      worlds: [{ id: "w-1", seed_prompt: "A", status: "running", description: "" }],
      links: [{ world_a: "w-1", world_b: "w-2", strength: 0.7, count: 4 }],
    }),
  })) as unknown as typeof fetch;

  try {
    await useMultiverseStore.getState().fetchWorldMap(0.3, 2);
  } finally {
    global.fetch = originalFetch;
  }

  const state = useMultiverseStore.getState();
  assert.equal(state.worldsMap?.links.length, 1);
  assert.equal(state.worldsMap?.links[0].count, 4);
});

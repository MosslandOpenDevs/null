import assert from "node:assert/strict";
import test from "node:test";

import { useStrataStore } from "../src/stores/strata.ts";

function resetStrataStore() {
  useStrataStore.setState({
    strata: [],
    comparison: null,
    comparisonLoading: false,
  });
}

test("fetchStrata loads timeline rows when api is ok", async () => {
  resetStrataStore();
  const originalFetch = global.fetch;
  global.fetch = (async () => ({
    ok: true,
    json: async () => [
      {
        id: "s-1",
        world_id: "w-1",
        epoch: 3,
        summary: "Epoch 3 summary",
        emerged_concepts: ["trade pact"],
        faded_concepts: [],
        dominant_themes: ["trade"],
      },
    ],
  })) as unknown as typeof fetch;

  try {
    await useStrataStore.getState().fetchStrata("w-1");
  } finally {
    global.fetch = originalFetch;
  }

  const state = useStrataStore.getState();
  assert.equal(state.strata.length, 1);
  assert.equal(state.strata[0].epoch, 3);
});

test("fetchComparison stores compare payload", async () => {
  resetStrataStore();
  const originalFetch = global.fetch;
  global.fetch = (async () => ({
    ok: true,
    json: async () => ({
      world_id: "w-1",
      from_epoch: 2,
      to_epoch: 3,
      from_summary: "old",
      to_summary: "new",
      added_themes: ["stability"],
      removed_themes: ["panic"],
      persisted_themes: ["trade"],
      newly_emerged_concepts: ["pact"],
      newly_faded_concepts: ["panic"],
    }),
  })) as unknown as typeof fetch;

  try {
    await useStrataStore.getState().fetchComparison("w-1", 2, 3);
  } finally {
    global.fetch = originalFetch;
  }

  const state = useStrataStore.getState();
  assert.equal(state.comparisonLoading, false);
  assert.equal(state.comparison?.from_epoch, 2);
  assert.deepEqual(state.comparison?.added_themes, ["stability"]);
});

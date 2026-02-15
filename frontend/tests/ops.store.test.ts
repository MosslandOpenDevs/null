import assert from "node:assert/strict";
import test from "node:test";

import { useOpsStore } from "../src/stores/ops.ts";

function resetOpsStore() {
  useOpsStore.setState({
    metrics: null,
    loading: false,
  });
}

test("fetchMetrics stores ops snapshot when api is ok", async () => {
  resetOpsStore();
  const originalFetch = global.fetch;
  global.fetch = (async () => ({
    ok: true,
    json: async () => ({
      generated_at: "2026-02-14T10:00:00Z",
      worlds: [{ status: "running", count: 2 }],
      active_runners: 1,
      loops: [],
      runners: [],
      queues: {
        translator_pending_conversations: 1,
        translator_pending_wiki_pages: 2,
        translator_pending_strata: 3,
        generating_worlds: 0,
      },
      alerts: [],
    }),
  })) as unknown as typeof fetch;

  try {
    await useOpsStore.getState().fetchMetrics();
  } finally {
    global.fetch = originalFetch;
  }

  const state = useOpsStore.getState();
  assert.equal(state.loading, false);
  assert.equal(state.metrics?.active_runners, 1);
  assert.equal(state.metrics?.worlds[0].count, 2);
});

import assert from "node:assert/strict";
import test from "node:test";

import { summarizeOpsHealth, useOpsStore } from "../src/stores/ops.ts";

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

test("summarizeOpsHealth classifies degraded and critical states", () => {
  const degraded = summarizeOpsHealth({
    generated_at: "2026-03-03T00:00:00Z",
    worlds: [{ status: "running", count: 2 }],
    active_runners: 2,
    loops: [{ name: "translator", status: "stopped", restart_count: 1 }],
    runners: [{ world_id: "w1", status: "running", ticks_total: 30, tick_failures: 0, success_rate: 1 }],
    queues: {
      translator_pending_conversations: 10,
      translator_pending_wiki_pages: 8,
      translator_pending_strata: 4,
      generating_worlds: 0,
    },
    alerts: [{ code: "ops_warn", severity: "warning", message: "queue spike", context: {} }],
  });

  assert.equal(degraded.level, "degraded");
  assert.equal(degraded.warningAlerts, 1);
  assert.equal(degraded.criticalAlerts, 0);
  assert.equal(degraded.unhealthyLoops, 1);
  assert.equal(degraded.backlogSize, 22);

  const critical = summarizeOpsHealth({
    generated_at: "2026-03-03T00:00:00Z",
    worlds: [{ status: "running", count: 2 }],
    active_runners: 2,
    loops: [{ name: "translator", status: "running", restart_count: 1 }],
    runners: [{ world_id: "w1", status: "running", ticks_total: 30, tick_failures: 2, success_rate: 0.9 }],
    queues: {
      translator_pending_conversations: 1,
      translator_pending_wiki_pages: 1,
      translator_pending_strata: 0,
      generating_worlds: 0,
    },
    alerts: [{ code: "ops_critical", severity: "critical", message: "runner failing", context: {} }],
  });

  assert.equal(critical.level, "critical");
  assert.equal(critical.criticalAlerts, 1);
  assert.equal(critical.failingRunners, 1);
});

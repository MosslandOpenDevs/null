import assert from "node:assert/strict";
import test from "node:test";

import { useSimulationStore, type WSEvent } from "../src/stores/simulation.ts";

function resetSimulationStore() {
  useSimulationStore.setState({
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
  });
}

function makeEvent(index: number): WSEvent {
  return {
    type: `old-${index}`,
    timestamp: `2026-02-12T00:00:${String(index % 60).padStart(2, "0")}Z`,
    epoch: 0,
    payload: { tick: index },
  };
}

test("addEvent keeps only latest 501 events and updates world tick/epoch", () => {
  resetSimulationStore();

  useSimulationStore.setState({
    world: {
      id: "w1",
      seed_prompt: "test",
      config: {},
      status: "running",
      current_epoch: 1,
      current_tick: 1,
    },
    events: Array.from({ length: 600 }, (_, i) => makeEvent(i)),
  });

  useSimulationStore.getState().addEvent({
    type: "agent.message",
    timestamp: "2026-02-12T10:00:00Z",
    epoch: 5,
    payload: { tick: 42 },
  });

  const state = useSimulationStore.getState();
  assert.equal(state.events.length, 501);
  assert.equal(state.events[0].type, "old-100");
  assert.equal(state.events[500].type, "agent.message");
  assert.equal(state.world?.current_epoch, 5);
  assert.equal(state.world?.current_tick, 42);
});

test("addEvent with herald.announcement appends herald message", () => {
  resetSimulationStore();

  const originalSetTimeout = global.setTimeout;
  global.setTimeout = (() => 0) as unknown as typeof setTimeout;
  try {
    useSimulationStore.getState().addEvent({
      type: "herald.announcement",
      timestamp: "2026-02-12T10:00:01Z",
      epoch: 1,
      payload: { text: "Epoch shift detected" },
    });
  } finally {
    global.setTimeout = originalSetTimeout;
  }

  const state = useSimulationStore.getState();
  assert.equal(state.heraldMessages.length, 1);
  assert.equal(state.heraldMessages[0].text, "Epoch shift detected");
});

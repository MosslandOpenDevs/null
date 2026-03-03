import { create } from "zustand";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3301";

export interface OpsWorldStatus {
  status: string;
  count: number;
}

export interface OpsLoop {
  name: string;
  status: string;
  restart_count: number;
  last_started_at?: string | null;
  last_error_at?: string | null;
  last_error?: string | null;
}

export interface OpsRunner {
  world_id: string;
  status: string;
  ticks_total: number;
  tick_failures: number;
  success_rate: number;
  last_duration_ms?: number | null;
  avg_duration_ms?: number | null;
  last_tick_delay_ms?: number | null;
  last_seen_at?: string | null;
}

export interface OpsQueue {
  translator_pending_conversations: number;
  translator_pending_wiki_pages: number;
  translator_pending_strata: number;
  generating_worlds: number;
}

export interface OpsAlert {
  code: string;
  severity: "critical" | "warning" | "info" | string;
  message: string;
  context: Record<string, unknown>;
}

export interface OpsMetrics {
  generated_at: string;
  worlds: OpsWorldStatus[];
  active_runners: number;
  loops: OpsLoop[];
  runners: OpsRunner[];
  queues: OpsQueue;
  alerts: OpsAlert[];
}

export interface OpsHealthSummary {
  criticalAlerts: number;
  warningAlerts: number;
  unhealthyLoops: number;
  failingRunners: number;
  backlogSize: number;
  level: "healthy" | "degraded" | "critical";
}

export function summarizeOpsHealth(metrics: OpsMetrics | null): OpsHealthSummary {
  if (!metrics) {
    return {
      criticalAlerts: 0,
      warningAlerts: 0,
      unhealthyLoops: 0,
      failingRunners: 0,
      backlogSize: 0,
      level: "healthy",
    };
  }

  const criticalAlerts = metrics.alerts.filter((alert) => alert.severity === "critical").length;
  const warningAlerts = metrics.alerts.filter((alert) => alert.severity === "warning").length;
  const unhealthyLoops = metrics.loops.filter((loop) => loop.status !== "running").length;
  const failingRunners = metrics.runners.filter((runner) => runner.tick_failures > 0).length;
  const backlogSize =
    metrics.queues.translator_pending_conversations +
    metrics.queues.translator_pending_wiki_pages +
    metrics.queues.translator_pending_strata +
    metrics.queues.generating_worlds;

  const level: OpsHealthSummary["level"] =
    criticalAlerts > 0 || failingRunners > 0
      ? "critical"
      : warningAlerts > 0 || unhealthyLoops > 0 || backlogSize >= 20
        ? "degraded"
        : "healthy";

  return {
    criticalAlerts,
    warningAlerts,
    unhealthyLoops,
    failingRunners,
    backlogSize,
    level,
  };
}

interface OpsState {
  metrics: OpsMetrics | null;
  loading: boolean;
  fetchMetrics: () => Promise<void>;
}

export const useOpsStore = create<OpsState>((set) => ({
  metrics: null,
  loading: false,

  fetchMetrics: async () => {
    set({ loading: true });
    try {
      const resp = await fetch(`${API_URL}/api/ops/metrics`);
      if (resp.ok) {
        const metrics = await resp.json();
        set({ metrics });
      }
    } catch {
      // endpoint may not be available
    } finally {
      set({ loading: false });
    }
  },
}));

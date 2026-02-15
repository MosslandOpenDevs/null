"use client";

import { useEffect } from "react";
import { useOpsStore } from "@/stores/ops";

const ALERT_COLOR: Record<string, string> = {
  critical: "text-danger border-danger/40",
  warning: "text-herald border-herald/40",
  info: "text-accent border-accent/40",
};

export function OpsTab() {
  const { metrics, loading, fetchMetrics } = useOpsStore();

  useEffect(() => {
    fetchMetrics();
    const timer = window.setInterval(fetchMetrics, 10_000);
    return () => window.clearInterval(timer);
  }, [fetchMetrics]);

  if (!metrics && loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-mono text-base text-hud-muted">LOADING OPS METRICS...</span>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="flex items-center justify-center h-full">
        <span className="font-mono text-base text-hud-muted">OPS METRICS UNAVAILABLE</span>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      <div className="font-mono text-sm uppercase tracking-[0.15em] text-hud-label">
        OPS SNAPSHOT
      </div>

      <div className="grid grid-cols-2 gap-2">
        <MetricBox label="ACTIVE RUNNERS" value={String(metrics.active_runners)} />
        <MetricBox label="ALERTS" value={String(metrics.alerts.length)} />
        <MetricBox label="GENESIS QUEUE" value={String(metrics.queues.generating_worlds)} />
        <MetricBox
          label="TRANSLATION BACKLOG"
          value={String(
            metrics.queues.translator_pending_conversations
              + metrics.queues.translator_pending_wiki_pages
              + metrics.queues.translator_pending_strata
          )}
        />
      </div>

      <div className="p-2 border border-hud-border">
        <div className="font-mono text-sm text-hud-label uppercase mb-1">WORLD STATUS</div>
        <div className="space-y-1">
          {metrics.worlds.map((item) => (
            <div key={item.status} className="flex items-center justify-between font-mono text-sm">
              <span className="text-hud-muted uppercase">{item.status}</span>
              <span className="text-hud-text">{item.count}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="p-2 border border-hud-border">
        <div className="font-mono text-sm text-hud-label uppercase mb-1">BACKGROUND LOOPS</div>
        <div className="space-y-1">
          {metrics.loops.map((loop) => (
            <div key={loop.name} className="flex items-center justify-between font-mono text-sm">
              <span className="text-hud-muted">{loop.name}</span>
              <span className="text-hud-text">
                {loop.status} (r:{loop.restart_count})
              </span>
            </div>
          ))}
        </div>
      </div>

      <div className="p-2 border border-hud-border">
        <div className="font-mono text-sm text-hud-label uppercase mb-1">ALERTS</div>
        {metrics.alerts.length === 0 ? (
          <div className="font-mono text-sm text-success">NO ACTIVE ALERTS</div>
        ) : (
          <div className="space-y-1">
            {metrics.alerts.map((alert, idx) => (
              <div
                key={`${alert.code}-${idx}`}
                className={`p-2 border font-mono text-sm ${ALERT_COLOR[alert.severity] || "text-hud-muted border-hud-border"}`}
              >
                <div className="uppercase">
                  [{alert.severity}] {alert.code}
                </div>
                <div className="normal-case mt-1">{alert.message}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="font-mono text-[11px] text-hud-label">
        updated: {new Date(metrics.generated_at).toLocaleTimeString()}
      </div>
    </div>
  );
}

function MetricBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-hud-border p-2">
      <div className="font-mono text-[11px] text-hud-label uppercase">{label}</div>
      <div className="font-mono text-sm text-accent mt-1">{value}</div>
    </div>
  );
}

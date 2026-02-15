#!/usr/bin/env python3
"""Simple HTTP load tester for NULL backend endpoints.

Usage:
  poetry run python scripts/loadtest.py --base-url http://localhost:3301 --requests 600 --concurrency 30
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import httpx


@dataclass
class EndpointStats:
    latencies_ms: list[float] = field(default_factory=list)
    ok: int = 0
    failed: int = 0
    status_counts: dict[int, int] = field(default_factory=lambda: defaultdict(int))

    def record(self, latency_ms: float, status_code: int | None) -> None:
        self.latencies_ms.append(latency_ms)
        if status_code is None:
            self.failed += 1
            return
        self.status_counts[status_code] += 1
        if 200 <= status_code < 300:
            self.ok += 1
        else:
            self.failed += 1


def percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * p
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return sorted_values[low]
    weight = rank - low
    return sorted_values[low] * (1 - weight) + sorted_values[high] * weight


async def discover_world_id(client: httpx.AsyncClient) -> str | None:
    try:
        resp = await client.get("/api/worlds")
        if not resp.is_success:
            return None
        items = resp.json()
        if isinstance(items, list) and items:
            first = items[0]
            if isinstance(first, dict):
                world_id = first.get("id")
                if isinstance(world_id, str):
                    return world_id
    except Exception:
        return None
    return None


def build_endpoints(world_id: str | None) -> list[str]:
    endpoints = [
        "/health",
        "/api/worlds",
        "/api/ops/metrics",
        "/api/ops/alerts",
        "/api/multiverse/worlds/map?min_strength=0.2&min_count=1",
    ]
    if world_id:
        endpoints.extend(
            [
                f"/api/worlds/{world_id}/feed?limit=20",
                f"/api/worlds/{world_id}/strata",
                f"/api/worlds/{world_id}/strata/compare",
                f"/api/multiverse/worlds/{world_id}/neighbors?min_strength=0.2",
            ]
        )
    return endpoints


async def run_load(
    *,
    base_url: str,
    total_requests: int,
    concurrency: int,
    timeout_seconds: float,
    world_id: str | None,
) -> dict:
    endpoint_stats: dict[str, EndpointStats] = {}

    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(base_url=base_url, timeout=timeout) as client:
        # Warmup health check
        await client.get("/health")

        active_world_id = world_id or await discover_world_id(client)
        endpoints = build_endpoints(active_world_id)

        queue: asyncio.Queue[str] = asyncio.Queue()
        for i in range(total_requests):
            queue.put_nowait(endpoints[i % len(endpoints)])

        start = time.perf_counter()

        async def worker() -> None:
            while True:
                try:
                    endpoint = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return

                t0 = time.perf_counter()
                status_code: int | None = None
                try:
                    resp = await client.get(endpoint)
                    status_code = resp.status_code
                except Exception:
                    status_code = None
                latency_ms = (time.perf_counter() - t0) * 1000.0

                stats = endpoint_stats.setdefault(endpoint, EndpointStats())
                stats.record(latency_ms, status_code)
                queue.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(max(1, concurrency))]
        await queue.join()
        await asyncio.gather(*workers)
        elapsed = time.perf_counter() - start

    all_latencies = [lat for stats in endpoint_stats.values() for lat in stats.latencies_ms]
    all_latencies_sorted = sorted(all_latencies)
    total_ok = sum(stats.ok for stats in endpoint_stats.values())
    total_failed = sum(stats.failed for stats in endpoint_stats.values())
    total_done = total_ok + total_failed

    endpoint_summary = {}
    for endpoint, stats in sorted(endpoint_stats.items(), key=lambda item: item[0]):
        values = sorted(stats.latencies_ms)
        endpoint_summary[endpoint] = {
            "requests": len(values),
            "ok": stats.ok,
            "failed": stats.failed,
            "success_rate": round(stats.ok / len(values), 4) if values else 0.0,
            "latency_ms": {
                "avg": round(sum(values) / len(values), 2) if values else 0.0,
                "p50": round(percentile(values, 0.5), 2) if values else 0.0,
                "p95": round(percentile(values, 0.95), 2) if values else 0.0,
                "max": round(max(values), 2) if values else 0.0,
            },
            "status_codes": dict(sorted(stats.status_counts.items(), key=lambda item: item[0])),
        }

    overall_success_rate = (total_ok / total_done) if total_done else 0.0
    alerts: list[str] = []
    if overall_success_rate < 0.98:
        alerts.append(f"overall_success_rate_below_target:{overall_success_rate:.3f}")
    if all_latencies_sorted and percentile(all_latencies_sorted, 0.95) > 1000:
        alerts.append(f"overall_p95_latency_high:{percentile(all_latencies_sorted, 0.95):.2f}ms")

    return {
        "base_url": base_url,
        "world_id": active_world_id,
        "requests": total_requests,
        "concurrency": concurrency,
        "duration_seconds": round(elapsed, 3),
        "throughput_rps": round(total_done / elapsed, 2) if elapsed > 0 else 0.0,
        "overall": {
            "ok": total_ok,
            "failed": total_failed,
            "success_rate": round(overall_success_rate, 4),
            "latency_ms": {
                "avg": round(sum(all_latencies_sorted) / len(all_latencies_sorted), 2) if all_latencies_sorted else 0.0,
                "p50": round(percentile(all_latencies_sorted, 0.5), 2) if all_latencies_sorted else 0.0,
                "p95": round(percentile(all_latencies_sorted, 0.95), 2) if all_latencies_sorted else 0.0,
                "max": round(max(all_latencies_sorted), 2) if all_latencies_sorted else 0.0,
            },
        },
        "endpoints": endpoint_summary,
        "alerts": alerts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NULL backend load test")
    parser.add_argument("--base-url", default="http://localhost:3301")
    parser.add_argument("--requests", type=int, default=400)
    parser.add_argument("--concurrency", type=int, default=20)
    parser.add_argument("--timeout-seconds", type=float, default=8.0)
    parser.add_argument("--world-id", default=None)
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    parser.add_argument("--dry-run", action="store_true", help="Do not send HTTP requests; output planned benchmark config")
    return parser.parse_args()


def write_summary(summary: dict, out_path: str | None) -> None:
    payload = json.dumps(summary, indent=2, ensure_ascii=True)
    print(payload)
    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")


async def _main() -> int:
    args = parse_args()

    if args.dry_run:
        summary = {
            "mode": "dry-run",
            "base_url": args.base_url,
            "requests": args.requests,
            "concurrency": args.concurrency,
            "world_id": args.world_id,
            "planned_endpoints": build_endpoints(args.world_id),
            "alerts": [],
        }
        write_summary(summary, args.out)
        return 0

    summary = await run_load(
        base_url=args.base_url,
        total_requests=args.requests,
        concurrency=args.concurrency,
        timeout_seconds=args.timeout_seconds,
        world_id=args.world_id,
    )
    write_summary(summary, args.out)

    # Fail non-zero when severe alerts exist (useful for CI gates).
    return 1 if summary["alerts"] else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))

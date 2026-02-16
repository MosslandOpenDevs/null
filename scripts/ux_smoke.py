#!/usr/bin/env python3
"""Full-stack UX smoke check for NULL.

This script validates that a human can at least:
1) Open home page
2) Create a world
3) Open world page
4) Query ops metrics

It can start backend/frontend servers automatically, or run against
already-running services.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class StepResult:
    name: str
    ok: bool
    detail: str


@dataclass
class HttpResult:
    status: int
    body_text: str
    json_body: Any | None


def _http_request(
    method: str,
    url: str,
    *,
    json_body: Any | None = None,
    timeout_seconds: float = 10.0,
) -> HttpResult:
    data: bytes | None = None
    headers = {"Accept": "application/json, text/html;q=0.9,*/*;q=0.8"}
    if json_body is not None:
        data = json.dumps(json_body, ensure_ascii=True).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url=url, method=method.upper(), data=data, headers=headers)
    try:
        with urlopen(req, timeout=timeout_seconds) as resp:
            status = getattr(resp, "status", resp.getcode())
            raw = resp.read()
    except HTTPError as exc:
        raw = exc.read() or b""
        status = exc.code
    except URLError as exc:
        raise RuntimeError(f"request_failed: {url}: {exc}") from exc

    body_text = raw.decode("utf-8", errors="replace")
    parsed: Any | None = None
    try:
        parsed = json.loads(body_text)
    except json.JSONDecodeError:
        parsed = None
    return HttpResult(status=status, body_text=body_text, json_body=parsed)


def _wait_until_ready(
    name: str,
    url: str,
    *,
    timeout_seconds: float,
    expected_status: int = 200,
) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error = "unknown"
    while time.monotonic() < deadline:
        try:
            res = _http_request("GET", url, timeout_seconds=2.0)
            if res.status == expected_status:
                return
            last_error = f"status={res.status}"
        except Exception as exc:  # pragma: no cover - best effort wait loop
            last_error = str(exc)
        time.sleep(0.5)
    raise RuntimeError(f"{name} not ready within {timeout_seconds}s ({last_error})")


def _start_process(command: str, cwd: Path) -> subprocess.Popen[str]:
    cmd = shlex.split(command)
    return subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _terminate_process(proc: subprocess.Popen[str], name: str) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)
    print(f"[cleanup] stopped {name} (pid={proc.pid})", file=sys.stderr)


def _drain_output(proc: subprocess.Popen[str]) -> str:
    if proc.stdout is None:
        return ""
    try:
        return proc.stdout.read() or ""
    except Exception:  # pragma: no cover - best effort diagnostics
        return ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NULL full-stack UX smoke check")
    parser.add_argument("--backend-url", default="http://localhost:3301")
    parser.add_argument("--frontend-url", default="http://localhost:3300")
    parser.add_argument("--locale", default="en")
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    parser.add_argument("--start-servers", action="store_true")
    parser.add_argument(
        "--backend-cmd",
        default="poetry run uvicorn src.null_engine.main:app --host 0.0.0.0 --port 3301",
    )
    parser.add_argument(
        "--frontend-cmd",
        default="pnpm --filter null-frontend dev",
    )
    return parser.parse_args()


def _emit_summary(summary: dict[str, Any], out_path: str | None) -> None:
    payload = json.dumps(summary, ensure_ascii=True, indent=2)
    print(payload)
    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    backend_dir = repo_root / "backend"
    started_at = datetime.now(timezone.utc).isoformat()
    started_monotonic = time.monotonic()

    backend_proc: subprocess.Popen[str] | None = None
    frontend_proc: subprocess.Popen[str] | None = None
    steps: list[StepResult] = []
    world_id: str | None = None

    try:
        if args.start_servers:
            backend_proc = _start_process(args.backend_cmd, backend_dir)
            frontend_proc = _start_process(args.frontend_cmd, repo_root)

        _wait_until_ready(
            "backend",
            f"{args.backend_url}/health",
            timeout_seconds=args.timeout_seconds,
        )
        steps.append(StepResult("backend_health", True, "GET /health == 200"))

        _wait_until_ready(
            "frontend",
            f"{args.frontend_url}/{args.locale}",
            timeout_seconds=args.timeout_seconds,
        )
        steps.append(StepResult("frontend_home_up", True, f"GET /{args.locale} == 200"))

        home = _http_request("GET", f"{args.frontend_url}/{args.locale}")
        if home.status != 200:
            steps.append(StepResult("home_render", False, f"status={home.status}"))
            raise RuntimeError("home page not reachable")
        if "NULL" not in home.body_text or "Launch New World" not in home.body_text:
            steps.append(
                StepResult(
                    "home_render",
                    False,
                    "expected UI markers not found (NULL / Launch New World)",
                )
            )
            raise RuntimeError("home markers missing")
        steps.append(StepResult("home_render", True, "core UI markers found"))

        create_world = _http_request(
            "POST",
            f"{args.backend_url}/api/worlds",
            json_body={"seed_prompt": "UX smoke world", "config": {"era": "test"}},
            timeout_seconds=20.0,
        )
        if create_world.status != 201 or not isinstance(create_world.json_body, dict):
            steps.append(
                StepResult(
                    "create_world",
                    False,
                    f"status={create_world.status}",
                )
            )
            raise RuntimeError("world create failed")
        world_id = str(create_world.json_body.get("id", ""))
        if not world_id:
            steps.append(StepResult("create_world", False, "missing id in response"))
            raise RuntimeError("world id missing")
        steps.append(StepResult("create_world", True, f"world_id={world_id}"))

        start_world = _http_request(
            "POST",
            f"{args.backend_url}/api/worlds/{world_id}/start",
            timeout_seconds=20.0,
        )
        if start_world.status != 200:
            steps.append(StepResult("start_world", False, f"status={start_world.status}"))
            raise RuntimeError("world start failed")
        steps.append(StepResult("start_world", True, "simulation started"))

        world_page = _http_request("GET", f"{args.frontend_url}/{args.locale}/world/{world_id}")
        if world_page.status != 200:
            steps.append(StepResult("world_page", False, f"status={world_page.status}"))
            raise RuntimeError("world page not reachable")
        steps.append(StepResult("world_page", True, "world route reachable"))

        ops = _http_request("GET", f"{args.backend_url}/api/ops/metrics")
        if ops.status != 200:
            steps.append(StepResult("ops_metrics", False, f"status={ops.status}"))
            raise RuntimeError("ops metrics failed")
        steps.append(StepResult("ops_metrics", True, "ops dashboard API reachable"))

        summary = {
            "ok": True,
            "world_id": world_id,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.monotonic() - started_monotonic, 3),
            "failed_steps": [step.name for step in steps if not step.ok],
            "steps": [step.__dict__ for step in steps],
        }
        _emit_summary(summary, args.out)
        return 0
    except Exception as exc:
        steps.append(StepResult("fatal", False, str(exc)))
        summary = {
            "ok": False,
            "world_id": world_id,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": round(time.monotonic() - started_monotonic, 3),
            "failed_steps": [step.name for step in steps if not step.ok],
            "steps": [step.__dict__ for step in steps],
        }
        _emit_summary(summary, args.out)
        if backend_proc and backend_proc.poll() is not None:
            print("\n[backend output]", file=sys.stderr)
            print(_drain_output(backend_proc), file=sys.stderr)
        if frontend_proc and frontend_proc.poll() is not None:
            print("\n[frontend output]", file=sys.stderr)
            print(_drain_output(frontend_proc), file=sys.stderr)
        return 1
    finally:
        if frontend_proc:
            _terminate_process(frontend_proc, "frontend")
        if backend_proc:
            _terminate_process(backend_proc, "backend")


if __name__ == "__main__":
    raise SystemExit(main())

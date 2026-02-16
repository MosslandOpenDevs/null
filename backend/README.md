# Backend (null-engine)

## Requirements
- Python `3.12`
- Poetry `2.x`

## Setup
```bash
poetry install
```

## Run
```bash
poetry run uvicorn src.null_engine.main:app --reload --host 0.0.0.0 --port 3301
```

## Quality Gates
```bash
poetry run ruff check src tests
poetry run pytest -q
```

## Operations Endpoints
- `GET /api/ops/metrics` — runtime loop/runner snapshot + queue backlog + derived alerts
- `GET /api/ops/alerts` — alerts-only view for dashboards/monitoring bots

Alert thresholds are configurable via `.env`:
- `OPS_RUNNER_TICKS_MIN_FOR_ALERT`
- `OPS_RUNNER_SUCCESS_RATE_THRESHOLD`
- `OPS_TRANSLATOR_BACKLOG_THRESHOLD`
- `OPS_GENERATING_WORLDS_THRESHOLD`

## Load Test
```bash
poetry run python scripts/loadtest.py --base-url http://localhost:3301 --requests 400 --concurrency 20
```

Tune alert thresholds when needed:
```bash
poetry run python scripts/loadtest.py --base-url http://localhost:3301 --requests 400 --concurrency 20 --target-success-rate 0.99 --target-p95-ms 800
```

CI artifact-only mode (no HTTP traffic):
```bash
poetry run python scripts/loadtest.py --dry-run --out ../artifacts/loadtest-report.json --history-out ../artifacts/loadtest-history.jsonl --trend-out ../artifacts/loadtest-trend.md --history-window 30 --no-fail-on-alert
```

Generate trend markdown from local benchmark history:
```bash
poetry run python scripts/loadtest.py --base-url http://localhost:3301 --requests 600 --concurrency 30 --history-out ../artifacts/loadtest-history.jsonl --trend-out ../artifacts/loadtest-trend.md
```

## Live Loadtest CI
- Workflow: `.github/workflows/loadtest-live.yml`
- Trigger: weekly schedule (`Monday 03:00 UTC`) or manual `workflow_dispatch`
- Secret: set `NULL_LOADTEST_BASE_URL` to enable real HTTP benchmark mode
- Optional Secret: set `NULL_LOADTEST_REPORT_WEBHOOK_URL` to push each run summary/trend to an external webhook
- Webhook payload: JSON with top-level `text` plus `loadtest` object (`run_url`, targets, overall metrics, alerts, trend markdown)
- Failure gate: in live mode, the workflow fails when alert thresholds are breached

## UX Smoke (Full Stack)
Run a practical smoke check that starts backend/frontend, creates a world, opens world route, and validates ops API:

```bash
cd ..
python3 scripts/ux_smoke.py --start-servers
```

Equivalent shortcuts:
- `make ux-smoke`
- `pnpm run test:ux-smoke`

CI integration:
- Workflow: `.github/workflows/ci.yml` (`ux-smoke` job)
- Backing services: PostgreSQL + Redis service containers
- Artifact: `ux-smoke-report` (`artifacts/ux-smoke-report.json`)
- GitHub job summary: duration + step-level PASS/FAIL table + failed-step highlights rendered to `GITHUB_STEP_SUMMARY`
- Pull request comment: CI bot upserts a single `UX Smoke (CI)` comment with latest run link/result

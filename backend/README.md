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

CI artifact-only mode (no HTTP traffic):
```bash
poetry run python scripts/loadtest.py --dry-run --out ../artifacts/loadtest-report.json --history-out ../artifacts/loadtest-history.jsonl --trend-out ../artifacts/loadtest-trend.md --history-window 30 --no-fail-on-alert
```

Generate trend markdown from local benchmark history:
```bash
poetry run python scripts/loadtest.py --base-url http://localhost:3301 --requests 600 --concurrency 30 --history-out ../artifacts/loadtest-history.jsonl --trend-out ../artifacts/loadtest-trend.md
```

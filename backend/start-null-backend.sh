#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:$PATH"
poetry run uvicorn src.null_engine.main:app --host 0.0.0.0 --port 6301

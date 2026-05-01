#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/bin:$PATH"

HOST="${NULL_BACKEND_HOST:-0.0.0.0}"
PORT="${NULL_BACKEND_PORT:-6301}"

if [[ ! "$HOST" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ && "$HOST" != "localhost" ]]; then
  echo "[null-backend] invalid host: $HOST" >&2
  exit 1
fi

if [[ ! "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
  echo "[null-backend] invalid port: $PORT" >&2
  exit 1
fi

if [[ "$HOST" == "0.0.0.1" ]]; then
  echo "[null-backend] invalid bind host 0.0.0.1 (did you mean 0.0.0.0?)" >&2
  exit 1
fi

exec poetry run uvicorn src.null_engine.main:app --host "$HOST" --port "$PORT"

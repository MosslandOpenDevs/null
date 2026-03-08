#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${NULL_BACKEND_URL:-http://localhost:6301}"
FRONTEND_URL="${NULL_FRONTEND_URL:-http://localhost:6001}"
RETRIES="${NULL_STARTUP_RETRIES:-20}"
RETRY_DELAY_SEC="${NULL_STARTUP_RETRY_DELAY_SEC:-2}"
MIN_WORLDS="${NULL_STARTUP_MIN_WORLDS:-1}"

http_code_with_retry() {
  local url="$1"
  local label="$2"
  local attempt=1

  while (( attempt <= RETRIES )); do
    local code
    code="$(curl -sS -o /dev/null -w '%{http_code}' -m 10 "$url" || echo 000)"
    if [[ "$code" == 2* || "$code" == 3* ]]; then
      echo "[startup-smoke] ${label} ready (${code})"
      return 0
    fi

    if (( attempt < RETRIES )); then
      echo "[startup-smoke] ${label} waiting (${code}), retry ${attempt}/${RETRIES} in ${RETRY_DELAY_SEC}s"
      sleep "$RETRY_DELAY_SEC"
    fi
    attempt=$((attempt + 1))
  done

  echo "[startup-smoke] ${label} failed readiness after ${RETRIES} attempts"
  return 1
}

verify_seed_worlds() {
  local url="${BACKEND_URL}/api/worlds"
  local payload
  payload="$(curl -sS -m 12 "$url")"

  python3 - "$MIN_WORLDS" "$payload" <<'PY'
import json
import sys

min_worlds = int(sys.argv[1])
raw = sys.argv[2].strip()
if not raw:
    raise SystemExit("empty_response")

try:
    data = json.loads(raw)
except json.JSONDecodeError as exc:
    raise SystemExit(f"invalid_json:{exc}")

if isinstance(data, list):
    worlds = data
elif isinstance(data, dict):
    if isinstance(data.get("items"), list):
        worlds = data["items"]
    elif isinstance(data.get("worlds"), list):
        worlds = data["worlds"]
    else:
        worlds = []
else:
    worlds = []

count = len(worlds)
if count < min_worlds:
    raise SystemExit(f"seed_underflow:{count}<{min_worlds}")

print(count)
PY
}

echo "[startup-smoke] checking service readiness"
http_code_with_retry "${BACKEND_URL}/health" "backend /health"
http_code_with_retry "${FRONTEND_URL}/" "frontend /"

echo "[startup-smoke] verifying seeded worlds"
world_count="$(verify_seed_worlds)"
echo "[startup-smoke] seed verification passed (worlds=${world_count}, min=${MIN_WORLDS})"

echo "[startup-smoke] all startup checks passed"
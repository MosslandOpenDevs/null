#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${NULL_BACKEND_URL:-http://localhost:6301}"
FRONTEND_URL="${NULL_FRONTEND_URL:-http://localhost:6001}"
FAILURES=0

a_check() {
  local label="$1"
  local target="$2"
  local path="$3"
  local tmp
  tmp="$(mktemp)"
  local code
  code=$(curl -sS -o "$tmp" -w '%{http_code}' -m 12 "$target$path" || echo 000)
  local len=0
  if [ -s "$tmp" ]; then
    len=$(wc -c < "$tmp")
  fi
  printf "  %s %s => %s (%s bytes)\n" "$label" "$path" "$code" "$len"
  if [[ "$code" != 2* && "$code" != 3* ]]; then
    echo "  !! non-2xx/3xx detected"
    FAILURES=$((FAILURES + 1))
  fi
  rm -f "$tmp"
}

echo "[null] checking backend: ${BACKEND_URL}"
for path in "/health"; do
  a_check backend "$BACKEND_URL" "$path"
done

echo "[null] checking frontend: ${FRONTEND_URL}"
for path in "/" "/en"; do
  a_check frontend "$FRONTEND_URL" "$path"
done

if [[ "$FAILURES" -gt 0 ]]; then
  echo "[null] FAILED checks: $FAILURES"
  exit 1
fi

echo "[null] all checks passed"

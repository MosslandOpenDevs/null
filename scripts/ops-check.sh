#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${NULL_BACKEND_URL:-http://localhost:6301}"
FRONTEND_URL="${NULL_FRONTEND_URL:-http://localhost:6001}"
BACKEND_RETRIES="${NULL_BACKEND_RETRIES:-3}"
BACKEND_RETRY_DELAY_SEC="${NULL_BACKEND_RETRY_DELAY_SEC:-2}"
ENABLE_BACKEND_SMOKE="${NULL_ENABLE_BACKEND_SMOKE:-1}"
REPORT_FILE="${NULL_OPS_REPORT_FILE:-}"
HISTORY_FILE="${NULL_OPS_HISTORY_FILE:-}"
FAILURES=0

run_check() {
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
  rm -f "$tmp"

  [[ "$code" == 2* || "$code" == 3* ]]
}

check_once() {
  local label="$1"
  local target="$2"
  local path="$3"

  if ! run_check "$label" "$target" "$path"; then
    echo "  !! non-2xx/3xx detected"
    FAILURES=$((FAILURES + 1))
    return 1
  fi

  return 0
}

check_with_retry() {
  local label="$1"
  local target="$2"
  local path="$3"
  local retries="$4"
  local delay_sec="$5"

  local attempt=1
  while (( attempt <= retries )); do
    if run_check "$label" "$target" "$path"; then
      return 0
    fi

    echo "  !! non-2xx/3xx detected"
    if (( attempt < retries )); then
      echo "  .. retry ${attempt}/${retries} after ${delay_sec}s"
      sleep "$delay_sec"
    fi

    attempt=$((attempt + 1))
  done

  FAILURES=$((FAILURES + 1))
  return 1
}

echo "[null] checking backend: ${BACKEND_URL}"
for path in "/health"; do
  check_with_retry backend "$BACKEND_URL" "$path" "$BACKEND_RETRIES" "$BACKEND_RETRY_DELAY_SEC" || true
done

if [[ "$ENABLE_BACKEND_SMOKE" == "1" ]]; then
  echo "[null] backend functional smoke checks"
  for path in "/openapi.json" "/api/worlds"; do
    check_with_retry backend-smoke "$BACKEND_URL" "$path" "$BACKEND_RETRIES" "$BACKEND_RETRY_DELAY_SEC" || true
  done
fi

echo "[null] checking frontend: ${FRONTEND_URL}"
for path in "/" "/en"; do
  check_once frontend "$FRONTEND_URL" "$path" || true
done

if [[ "$FAILURES" -gt 0 ]]; then
  status="fail"
  echo "[null] FAILED checks: $FAILURES"
  code=1
else
  status="ok"
  echo "[null] all checks passed"
  code=0
fi

summary="{\"service\":\"null\",\"status\":\"${status}\",\"failures\":${FAILURES},\"backend\":\"${BACKEND_URL}\",\"frontend\":\"${FRONTEND_URL}\",\"ts\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

if [[ -n "$REPORT_FILE" ]]; then
  printf '%s\n' "$summary" > "$REPORT_FILE"
  echo "[null] wrote ops report: ${REPORT_FILE}"
fi

if [[ -n "$HISTORY_FILE" ]]; then
  printf '%s\n' "$summary" >> "$HISTORY_FILE"
  echo "[null] appended ops history: ${HISTORY_FILE}"
fi

exit "$code"

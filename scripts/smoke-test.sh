#!/usr/bin/env bash
# End-to-end check of a running `docker compose` stack, through nginx.
# Used by CI and by `make smoke`. Note: it calls POST /train, so the model
# in the compose volume is retrained on whatever data is mounted.
set -euo pipefail

WEB="${WEB_URL:-http://localhost:8080}"
API="${API_URL:-http://localhost:8000}"

pass() { printf '  ok    %s\n' "$1"; }
fail() { printf '  FAIL  %s\n' "$1" >&2; exit 1; }

expect_status() {  # expect_status <description> <expected code> <curl args...>
  local description="$1" expected="$2"; shift 2
  local actual
  actual="$(curl -s -o /dev/null -w '%{http_code}' "$@")"
  [ "$actual" = "$expected" ] && pass "$description" || fail "$description (expected $expected, got $actual)"
}

expect_body() {  # expect_body <description> <text the body must contain> <curl args...>
  local description="$1" needle="$2"; shift 2
  local body
  body="$(curl -fsS "$@")" || fail "$description (request failed)"
  case "$body" in
    *"$needle"*) pass "$description" ;;
    *) fail "$description (response did not contain: $needle)" ;;
  esac
}

echo "SolarCast smoke test — web: $WEB, api: $API"

expect_status "frontend serves the dashboard"         200 "$WEB/"
expect_body   "frontend container is healthy"         "ok" "$WEB/healthz"
expect_body   "backend is live"                       '"status":"ok"' "$API/healthz"
expect_body   "backend is ready"                      '"status":"ready"' "$API/readyz"
expect_body   "history is served through nginx"       '"years":[' "$WEB/api/history"
expect_body   "training succeeds"                     '"status":"success"' -X POST "$WEB/api/train"
expect_body   "status reports a trained model"        '"modelTrained":true' "$WEB/api/status"
expect_body   "predictions are returned"              '"modelTrained":true' "$WEB/api/predict?months=3"
expect_status "out-of-range months are rejected"      422 "$WEB/api/predict?months=0"
expect_body   "backend exposes Prometheus metrics"    'solarcast_model_loaded 1.0' "$API/metrics"
expect_status "metrics are not exposed through nginx" 404 "$WEB/api/metrics"

echo "All checks passed."

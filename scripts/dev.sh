#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT/apps/api"
WEB_DIR="$ROOT/apps/web"
API_URL="http://127.0.0.1:8000"
WEB_URL="http://127.0.0.1:3000"

if [[ ! -x "$API_DIR/.venv/bin/uvicorn" ]]; then
  echo "Missing API environment. Create apps/api/.venv and install requirements." >&2
  exit 1
fi

if ! command -v bun >/dev/null 2>&1; then
  echo "Bun is required. Install it from https://bun.sh" >&2
  exit 1
fi

if [[ ! -d "$WEB_DIR/node_modules" ]] || [[ "$WEB_DIR/bun.lock" -nt "$WEB_DIR/node_modules" ]]; then
  echo "Syncing frontend dependencies..."
  (cd "$WEB_DIR" && bun install)
fi

# Stale Next dev on :3000 keeps old CSS after theme merges — replace it.
if lsof -iTCP:3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Stopping existing process on port 3000 (stale dev server)..."
  lsof -iTCP:3000 -sTCP:LISTEN -t | xargs kill 2>/dev/null || true
  sleep 1
fi

if lsof -iTCP:8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "Port 8000 is already in use. Stop that process and retry." >&2
  exit 1
fi

# Bust Turbopack dev cache so globals.css token changes always apply.
rm -rf "$WEB_DIR/.next/dev"

export WORLD_CUP_DATA_MODE="${WORLD_CUP_DATA_MODE:-processed}"
export NEXT_PUBLIC_API_BASE_URL="$API_URL"
export NEXT_PUBLIC_WCO_SIMULATIONS="${NEXT_PUBLIC_WCO_SIMULATIONS:-1000}"
export NEXT_PUBLIC_WCO_ANALYTICS_SIMULATIONS="${NEXT_PUBLIC_WCO_ANALYTICS_SIMULATIONS:-500}"
export NEXT_PUBLIC_WCO_TEAM_PATH_SIMULATIONS="${NEXT_PUBLIC_WCO_TEAM_PATH_SIMULATIONS:-500}"

load_env_file() {
  local file="$1"
  if [[ -f "$file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$file"
    set +a
  fi
}

# API secrets (WCO_ADMIN_SYNC_KEY, FOOTBALL_DATA_API_TOKEN) must reach the backend.
load_env_file "$ROOT/.env"
load_env_file "$ROOT/apps/api/.env"
load_env_file "$ROOT/apps/web/.env.local"

cleanup() {
  trap - EXIT INT TERM
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "${WEB_PID:-}" ]] && kill "$WEB_PID" 2>/dev/null || true
  [[ -n "${API_PID:-}" ]] && wait "$API_PID" 2>/dev/null || true
  [[ -n "${WEB_PID:-}" ]] && wait "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting API..."
(
  cd "$API_DIR"
  exec .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
API_PID=$!

echo "Starting web app..."
(
  cd "$WEB_DIR"
  exec bun run dev --hostname 127.0.0.1 --port 3000
) &
WEB_PID=$!

for _ in {1..60}; do
  if curl --silent --fail "$API_URL/health" >/dev/null 2>&1 \
    && curl --silent --fail "$WEB_URL" >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null || ! kill -0 "$WEB_PID" 2>/dev/null; then
    echo "A development server stopped during startup." >&2
    exit 1
  fi
  sleep 1
done

if ! curl --silent --fail "$API_URL/health" >/dev/null 2>&1 \
  || ! curl --silent --fail "$WEB_URL" >/dev/null 2>&1; then
  echo "Development servers did not become ready in time." >&2
  exit 1
fi

echo
echo "World Cup Oracle ready: $WEB_URL"
echo "Forecast profile: ${NEXT_PUBLIC_WCO_SIMULATIONS} tournament / ${NEXT_PUBLIC_WCO_ANALYTICS_SIMULATIONS} analytics simulations"
echo "Press Ctrl+C to stop both servers."

if [[ "${WCO_NO_OPEN:-0}" != "1" ]] && command -v open >/dev/null 2>&1; then
  open "$WEB_URL"
fi

while kill -0 "$API_PID" 2>/dev/null && kill -0 "$WEB_PID" 2>/dev/null; do
  sleep 1
done

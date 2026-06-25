# World Cup Oracle

World Cup Oracle is a FastAPI + Next.js World Cup simulation dashboard.

## Quick Start

Run both servers with one command:

```bash
./scripts/dev.sh
```

The launcher opens `http://127.0.0.1:3000`, enables hot reload, and uses a
small simulation profile so pages load quickly while testing. Press `Ctrl+C`
to stop both servers.

Override interactive scenario simulation counts when needed:

```bash
NEXT_PUBLIC_WCO_SIMULATIONS=5000 \
NEXT_PUBLIC_WCO_ANALYTICS_SIMULATIONS=1000 \
./scripts/dev.sh
```

Tournament forecasts enforce at least 1,000 simulations. Smaller samples make
the favorites table unstable and can contradict the deterministic bracket.

Dashboard, groups, and team probability pages read
`data/processed/forecast_snapshot.json`. Normal page loads do not run Monte
Carlo simulations. Result sync rebuilds this shared 5,000-run snapshot once
after new scores are published.

Set `WCO_NO_OPEN=1` to prevent the browser from opening automatically.

## Data Mode

Backend defaults to real processed World Cup 2026 data:

```bash
WORLD_CUP_DATA_MODE=processed
```

Use sample data only for tests/dev fallback:

```bash
WORLD_CUP_DATA_MODE=sample
```

The app reads published JSON snapshots from `data/processed`. Forecast controls
rerun simulations against that snapshot; they do not silently fetch results.

## Refresh Data

Configure the backend result sync in repo-root `.env` (or `apps/web/.env.local`
when using `./scripts/dev.sh`):

```bash
WCO_ADMIN_SYNC_KEY=choose-a-long-random-secret
FOOTBALL_DATA_API_TOKEN=your-football-data-token
```

These variables are read by the FastAPI process, not by the Next.js client.

The dashboard's **Sync match results** button calls the protected
`POST /admin/sync/results` endpoint. It tries football-data.org first and falls
back to FIFA's public match feed. Incoming files are staged and validated
before publication; contradictory published scores abort the refresh.

Ranking and model-training refreshes remain separate CLI workflows. A result
sync never retrains or silently changes the selected forecasting model.

## Run Backend

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload
```

Backend validation:

```bash
cd apps/api
source .venv/bin/activate
bash ../../scripts/clean_pycache.sh
pytest
```

Optional one-time setup to clear Python caches on every commit:

```bash
bash scripts/install-git-hooks.sh
```

## Run Frontend

Use Bun, not npm:

```bash
cd apps/web
bun install
bun run dev
bun run lint
bun run build
```

Set frontend API target:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

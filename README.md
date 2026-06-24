# World Cup Oracle

World Cup Oracle is a FastAPI + Next.js World Cup simulation dashboard.

## Data Mode

Backend defaults to real processed World Cup 2026 data:

```bash
WORLD_CUP_DATA_MODE=processed
```

Use sample data only for tests/dev fallback:

```bash
WORLD_CUP_DATA_MODE=sample
```

Runtime does not fetch internet. App reads checked-in JSON from
`data/processed`.

## Refresh Data

```bash
python scripts/ingest/fetch_worldcup_fifa.py
python scripts/ingest/fetch_fifa_rankings.py
python scripts/ingest/fetch_elo_ratings.py
python scripts/ingest/validate_processed_data.py
```

If a source blocks automation, save normalized raw files under `data/raw/` and
rerun the relevant script with `--raw-file`.

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

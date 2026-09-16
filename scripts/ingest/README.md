# World Cup Data Ingestion

These scripts acquire or ingest World Cup 2026 data and write normalized files
to `data/processed`.

## Sources

- FIFA World Cup 26 scores and fixtures: `https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures`
- FIFA/Coca-Cola Men's World Ranking: `https://inside.fifa.com/fifa-world-ranking/men`
- World Football Elo Ratings: `https://www.eloratings.net/`
- Transfermarkt Datasets: `https://github.com/dcaribou/transfermarkt-datasets`

## Commands

```bash
python scripts/ingest/fetch_worldcup_fifa.py
python scripts/ingest/fetch_fifa_rankings.py
python scripts/ingest/fetch_elo_ratings.py
python scripts/ingest/fetch_historical_results.py
python scripts/ingest/fetch_transfermarkt_features.py
python scripts/ingest/validate_processed_data.py
```

Local raw-file fallback:

```bash
python scripts/ingest/fetch_worldcup_fifa.py --raw-file data/raw/fifa/worldcup_2026.json
python scripts/ingest/fetch_fifa_rankings.py --raw-file data/raw/ratings/fifa_rankings.json
python scripts/ingest/fetch_elo_ratings.py --raw-file data/raw/ratings/elo_ratings.csv
python scripts/ingest/fetch_historical_results.py --raw-file data/raw/results/international_results.csv
python scripts/ingest/fetch_transfermarkt_features.py --national-teams-file data/raw/ratings/national_teams.csv.gz --players-file data/raw/ratings/players.csv.gz
```

Processed outputs:

- `data/processed/teams.json`
- `data/processed/groups.json`
- `data/processed/fixtures.json`
- `data/processed/results.json`
- `data/processed/ratings.json`
- `data/processed/metadata.json`
- `data/processed/model_parameters.json`
- `data/processed/squad_features.json`

If a source blocks automated access, save a manually downloaded normalized file
under `data/raw/fifa/` or `data/raw/ratings/` and rerun the relevant script with
`--raw-file`.

Runtime code never fetches the internet. The backend reads checked-in processed
JSON files.

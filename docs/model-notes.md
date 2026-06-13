# Model Notes

Current model is still baseline simulation:

- Elo win/draw/loss model.
- Poisson score model.
- No ML model yet.
- No ensemble model yet.

Ratings currently use processed external/rank-derived data recorded in
`data/processed/ratings.json` and `data/processed/metadata.json`.

`ratings_are_official=false` means ratings are external or derived, not an
official FIFA team-strength model.

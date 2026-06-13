# Model Notes

Current model is still baseline simulation:

- Elo win/draw/loss model.
- Poisson score model.
- Open-data calibrated Elo model trained from senior international results.
- No ML model yet.
- No ensemble model yet.

Ratings currently use processed external/rank-derived data recorded in
`data/processed/ratings.json` and `data/processed/metadata.json`.

`ratings_are_official=false` means ratings are external or derived, not an
official FIFA team-strength model.

`data/processed/model_parameters.json` contains open-data Elo parameters derived
from international match results since 2018. It improves credibility over pure
rank-derived ratings, but it is still not player-level, xG, injury, or market
data.

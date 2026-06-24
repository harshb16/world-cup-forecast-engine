# Model Notes

Current public default:

- Open-data calibrated Elo model trained from senior international results.

Other available models:

- Elo and Poisson baselines.
- Dixon-Coles scoreline baseline with a fixed low-score correction.
- Oracle v2 squad-aware ensemble, experimental.
- Gradient boosting classifier, experimental; training uses synthetic labels.
- Oracle v3 blended ensemble, experimental.

Oracle v2, GBM, and Oracle v3 remain comparison models. They should not be
presented as better than calibrated Elo until rolling historical holdout tests
show a repeatable gain.

Ratings currently use processed external/rank-derived data recorded in
`data/processed/ratings.json` and `data/processed/metadata.json`.

`ratings_are_official=false` means ratings are external or derived, not an
official FIFA team-strength model.

`data/processed/model_parameters.json` contains open-data Elo parameters derived
from international match results since 2018. It improves credibility over pure
rank-derived ratings, but it is still not player-level, xG, injury, or market
data.

"""Public model metadata."""

from app.models.schemas import ModelMetadataResponse


def list_model_metadata() -> list[ModelMetadataResponse]:
    """Return supported model descriptions for public transparency pages."""
    return [
        ModelMetadataResponse(
            id="elo",
            name="Elo win/draw/loss baseline",
            is_ml=False,
            maturity="baseline",
            inputs=[
                "team rating",
                "opponent rating",
            ],
            assumptions=[
                "Rating gap maps to expected win share using an Elo curve.",
                "Draw probability starts from a fixed baseline and shrinks for large rating gaps.",
                "Scorelines are sampled from small representative win/draw score sets.",
            ],
            limitations=[
                "Does not use player availability, venue, travel, tactical style, or market data.",
                "Ratings are rank-derived in processed mode and are not official FIFA strength ratings.",
                "Scoreline shape is coarse; use the Poisson model for goal-based simulation.",
            ],
            supported_outputs=[
                "win/draw/loss probabilities",
                "simulated group match scorelines",
                "Monte Carlo stage probabilities",
            ],
        ),
        ModelMetadataResponse(
            id="poisson",
            name="Poisson scoreline baseline",
            is_ml=False,
            maturity="baseline",
            inputs=[
                "team rating",
                "opponent rating",
            ],
            assumptions=[
                "Ratings convert into expected goals for each team.",
                "Each team's goals are sampled independently from a Poisson distribution.",
                "Knockout draws are resolved by rating-weighted extra-time/penalty winner selection.",
            ],
            limitations=[
                "No Dixon-Coles correction yet, so low-score correlation is not adjusted.",
                "Does not learn from historical match features.",
                "Expected goals are rating-derived, not calibrated from team-level attacking and defensive data.",
            ],
            supported_outputs=[
                "expected goals",
                "win/draw/loss probabilities",
                "simulated scorelines",
                "Monte Carlo stage probabilities",
            ],
        ),
        ModelMetadataResponse(
            id="calibrated_elo",
            name="Open-data calibrated Elo",
            is_ml=False,
            maturity="production",
            inputs=[
                "open international match results since 2018",
                "active team identity",
                "home/neutral flag",
                "score margin",
            ],
            assumptions=[
                "Recent senior international results are a stronger strength signal than ranking position alone.",
                "Home advantage applies only to non-neutral matches in training.",
                "Goal margin scales rating updates without making blowouts dominate the model.",
            ],
            limitations=[
                "Still not an xG, player, injury, market, or event-data model.",
                "Team aliases and open-data coverage can miss edge cases.",
                "Current calibration updates team ratings, not attack/defense shape.",
            ],
            supported_outputs=[
                "win/draw/loss probabilities",
                "favorite-path bracket reveal",
                "Monte Carlo stage probabilities",
                "team path distributions",
            ],
        ),
        ModelMetadataResponse(
            id="dixon_coles",
            name="Dixon-Coles Poisson model",
            is_ml=False,
            maturity="baseline",
            inputs=[
                "team rating",
                "opponent rating",
            ],
            assumptions=[
                "Expected goals are rating-derived (same as Poisson baseline).",
                "Joint score probabilities are corrected using the Dixon-Coles rho factor.",
                "Low-score scorelines (0-0, 0-1, 1-0, 1-1) are given adjusted probabilities.",
            ],
            limitations=[
                "Rho is fixed at -0.13 and not fitted from match data.",
                "Expected goals are not calibrated from team-level attacking and defensive data.",
                "Does not use player availability, venue, travel, or market data.",
            ],
            supported_outputs=[
                "expected goals",
                "win/draw/loss probabilities",
                "simulated scorelines with low-score correction",
                "Monte Carlo stage probabilities",
            ],
        ),
        ModelMetadataResponse(
            id="oracle_v2",
            name="Oracle v2 ensemble (experimental)",
            is_ml=False,
            maturity="experimental",
            inputs=[
                "rank-derived tournament rating",
                "open-data Elo from senior international results",
                "computed squad market-value strength",
                "attack/defense expected-goals shape",
            ],
            assumptions=[
                "Ratings, recent results, and squad value may complement one another.",
                "Expected goals should be generated from separate attack and defense strength.",
                "Favorite paths use projected group tables, not raw third-place strength sorting.",
                "Knockout rounds apply a lower expected-goals scale than group-stage matches.",
            ],
            limitations=[
                "No private injury, lineup, or event feed is used.",
                "Squad-value coverage depends on the free Transfermarkt dataset refresh.",
                "xG is still a computed proxy until direct international xG coverage is available.",
                "The blend has not shown a repeatable holdout gain over calibrated Elo.",
            ],
            supported_outputs=[
                "expected goals",
                "win/draw/loss probabilities",
                "simulated scorelines",
                "favorite-path bracket reveal",
                "Monte Carlo stage probabilities",
            ],
        ),
        ModelMetadataResponse(
            id="gbm",
            name="Gradient boosting classifier (experimental)",
            is_ml=True,
            maturity="experimental",
            inputs=[
                "rating difference",
                "team ratings",
                "absolute rating gap",
            ],
            assumptions=[
                "Historical and synthetic international fixtures train a calibrated GBM.",
                "Scorelines are sampled from Oracle v2 expected goals after W/D/L draw.",
            ],
            limitations=[
                "Training data is sparse for the 2026 tournament window.",
                "Synthetic labels supplement real results until more fixtures finish.",
                "Feature set is minimal compared with full event or xG models.",
            ],
            supported_outputs=[
                "win/draw/loss probabilities",
                "simulated scorelines",
                "Monte Carlo stage probabilities",
            ],
        ),
        ModelMetadataResponse(
            id="oracle_v3",
            name="Oracle v3 ensemble (experimental)",
            is_ml=True,
            maturity="experimental",
            inputs=[
                "Dixon-Coles scoreline model",
                "Oracle v2 squad-aware model",
                "GBM classifier (when artifact available)",
            ],
            assumptions=[
                "Blended W/D/L probabilities are intended to combine complementary model signals.",
                "Default weights are 35% Dixon-Coles, 35% Oracle v2, 30% GBM.",
                "Falls back to 50/50 Dixon-Coles + Oracle v2 when GBM artifact is missing.",
            ],
            limitations=[
                "Ensemble weights are fixed, not re-fit after every matchday.",
                "GBM availability depends on scripts/train_gbm_model.py being run.",
                "No repeatable historical holdout gain over calibrated Elo has been established.",
            ],
            supported_outputs=[
                "win/draw/loss probabilities",
                "simulated scorelines",
                "Monte Carlo stage probabilities",
                "favorite-path bracket reveal",
            ],
        ),
    ]

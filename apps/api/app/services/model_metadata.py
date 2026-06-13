"""Public model metadata."""

from app.models.schemas import ModelMetadataResponse


def list_model_metadata() -> list[ModelMetadataResponse]:
    """Return supported model descriptions for public transparency pages."""
    return [
        ModelMetadataResponse(
            id="elo",
            name="Elo win/draw/loss baseline",
            is_ml=False,
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
    ]

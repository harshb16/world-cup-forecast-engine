"""Tests for checked-in model parameter data."""

from app.services.data_loader import load_model_parameters, load_squad_features


def test_processed_model_parameters_cover_active_teams() -> None:
    parameters = load_model_parameters("processed")
    ratings = parameters["team_ratings"]

    assert len(ratings) == 48
    assert all(item["rating"] > 0 for item in ratings)
    assert not any(item["fallback_used"] for item in ratings)


def test_processed_model_parameters_include_open_data_source() -> None:
    parameters = load_model_parameters("processed")

    assert "international_results" in parameters["source"]["url"]
    assert parameters["training_window_start"] == "2018-01-01"


def test_processed_squad_features_cover_active_teams() -> None:
    features = load_squad_features("processed")

    assert len(features) == 48
    assert all(item["squad_power"] > 0 for item in features.values())
    assert features["FRANCE"]["squad_power"] > features["IRN"]["squad_power"]

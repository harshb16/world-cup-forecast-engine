"""Tests for processed data mode defaults."""

from fastapi.testclient import TestClient

from app.core.config import get_data_mode
from app.main import app
from app.services.data_loader import load_tournament


client = TestClient(app)


def test_default_data_mode_is_processed(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WORLD_CUP_DATA_MODE", raising=False)

    assert get_data_mode() == "processed"


def test_teams_returns_real_processed_teams(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WORLD_CUP_DATA_MODE", raising=False)
    response = client.get("/teams")
    names = {team["name"] for team in response.json()}

    assert response.status_code == 200
    assert {"Argentina", "Brazil", "England", "Mexico"}.issubset(names)


def test_groups_returns_real_group_a(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WORLD_CUP_DATA_MODE", raising=False)
    teams = {team["id"]: team["name"] for team in client.get("/teams").json()}
    group_a = next(group for group in client.get("/groups").json() if group["id"] == "A")

    assert [teams[team_id] for team_id in group_a["team_ids"]] == [
        "Mexico",
        "South Africa",
        "Korea Republic",
        "Czechia",
    ]


def test_fixtures_returns_processed_results(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WORLD_CUP_DATA_MODE", raising=False)
    fixtures = {fixture["id"]: fixture for fixture in client.get("/fixtures").json()}

    assert fixtures["A1"]["result"]["team_a_goals"] == 2
    assert fixtures["A1"]["result"]["team_b_goals"] == 0


def test_metadata_returns_real_data_status(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WORLD_CUP_DATA_MODE", raising=False)
    response = client.get("/metadata")

    assert response.status_code == 200
    assert response.json()["data_mode"] == "processed"
    assert response.json()["is_real_data"] is True


def test_simulate_works_with_processed_default(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WORLD_CUP_DATA_MODE", raising=False)
    response = client.post(
        "/simulate",
        json={"n_simulations": 3, "model_type": "elo", "seed": 1},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["data_mode"] == "processed"
    assert len(response.json()["teams"]) == 48


def test_explicit_sample_mode_still_loads() -> None:
    assert len(load_tournament("sample").teams) == 48

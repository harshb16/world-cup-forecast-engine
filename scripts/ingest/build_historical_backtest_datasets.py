#!/usr/bin/env python3
"""Build fixed historical World Cup backtest datasets (2018, 2014)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_ROOT = ROOT / "data" / "historical"

DATASETS = {
    "2018": {
        "name": "FIFA World Cup Russia 2018",
        "coverage_note": "Bootstrap dataset includes all 16 knockout matches from Russia 2018.",
        "teams": {
            "FRA": ("France", "C", 1880),
            "ARG": ("Argentina", "D", 1820),
            "URU": ("Uruguay", "A", 1780),
            "POR": ("Portugal", "B", 1790),
            "ESP": ("Spain", "B", 1830),
            "RUS": ("Russia", "A", 1720),
            "CRO": ("Croatia", "D", 1810),
            "DEN": ("Denmark", "C", 1760),
            "BRA": ("Brazil", "E", 1870),
            "MEX": ("Mexico", "F", 1740),
            "BEL": ("Belgium", "G", 1840),
            "JPN": ("Japan", "H", 1730),
            "SWE": ("Sweden", "F", 1750),
            "SUI": ("Switzerland", "E", 1770),
            "COL": ("Colombia", "H", 1765),
            "ENG": ("England", "G", 1825),
        },
        "fixtures": [
            ("R16-01", "Round of 16", "FRA", "ARG", 4, 3, "FRA"),
            ("R16-02", "Round of 16", "URU", "POR", 2, 1, "URU"),
            ("R16-03", "Round of 16", "ESP", "RUS", 1, 1, "RUS"),
            ("R16-04", "Round of 16", "CRO", "DEN", 1, 1, "CRO"),
            ("R16-05", "Round of 16", "BRA", "MEX", 2, 0, "BRA"),
            ("R16-06", "Round of 16", "BEL", "JPN", 3, 2, "BEL"),
            ("R16-07", "Round of 16", "SWE", "SUI", 1, 0, "SWE"),
            ("R16-08", "Round of 16", "COL", "ENG", 1, 1, "ENG"),
            ("QF-01", "Quarterfinal", "FRA", "URU", 2, 0, "FRA"),
            ("QF-02", "Quarterfinal", "BRA", "BEL", 1, 2, "BEL"),
            ("QF-03", "Quarterfinal", "SWE", "ENG", 0, 2, "ENG"),
            ("QF-04", "Quarterfinal", "RUS", "CRO", 2, 2, "CRO"),
            ("SF-01", "Semifinal", "FRA", "BEL", 1, 0, "FRA"),
            ("SF-02", "Semifinal", "CRO", "ENG", 2, 1, "CRO"),
            ("3RD-01", "Third place", "BEL", "ENG", 2, 0, "BEL"),
            ("FINAL-01", "Final", "FRA", "CRO", 4, 2, "FRA"),
        ],
    },
    "2014": {
        "name": "FIFA World Cup Brazil 2014",
        "coverage_note": "Bootstrap dataset includes all 16 knockout matches from Brazil 2014.",
        "teams": {
            "BRA": ("Brazil", "A", 1870),
            "CHI": ("Chile", "B", 1780),
            "COL": ("Colombia", "C", 1760),
            "URU": ("Uruguay", "D", 1775),
            "FRA": ("France", "E", 1830),
            "NGA": ("Nigeria", "F", 1700),
            "GER": ("Germany", "G", 1885),
            "ALG": ("Algeria", "H", 1680),
            "NED": ("Netherlands", "B", 1810),
            "MEX": ("Mexico", "A", 1740),
            "CRC": ("Costa Rica", "D", 1725),
            "GRE": ("Greece", "C", 1710),
            "ARG": ("Argentina", "F", 1840),
            "SUI": ("Switzerland", "E", 1765),
            "BEL": ("Belgium", "H", 1800),
            "USA": ("United States", "G", 1735),
        },
        "fixtures": [
            ("R16-01", "Round of 16", "BRA", "CHI", 1, 1, "BRA"),
            ("R16-02", "Round of 16", "COL", "URU", 2, 0, "COL"),
            ("R16-03", "Round of 16", "FRA", "NGA", 2, 0, "FRA"),
            ("R16-04", "Round of 16", "GER", "ALG", 2, 1, "GER"),
            ("R16-05", "Round of 16", "NED", "MEX", 2, 1, "NED"),
            ("R16-06", "Round of 16", "CRC", "GRE", 1, 1, "CRC"),
            ("R16-07", "Round of 16", "ARG", "SUI", 1, 0, "ARG"),
            ("R16-08", "Round of 16", "BEL", "USA", 2, 1, "BEL"),
            ("QF-01", "Quarterfinal", "FRA", "GER", 0, 1, "GER"),
            ("QF-02", "Quarterfinal", "BRA", "COL", 2, 1, "BRA"),
            ("QF-03", "Quarterfinal", "ARG", "BEL", 1, 0, "ARG"),
            ("QF-04", "Quarterfinal", "NED", "CRC", 0, 0, "NED"),
            ("SF-01", "Semifinal", "BRA", "GER", 1, 7, "GER"),
            ("SF-02", "Semifinal", "NED", "ARG", 0, 0, "ARG"),
            ("3RD-01", "Third place", "BRA", "NED", 0, 3, "NED"),
            ("FINAL-01", "Final", "GER", "ARG", 1, 0, "GER"),
        ],
    },
}


def _build_groups(team_entries: dict[str, tuple[str, str, int]]) -> list[dict[str, object]]:
    groups: dict[str, list[str]] = {}
    for team_id, (_, group_id, _) in team_entries.items():
        groups.setdefault(group_id, []).append(team_id)
    return [
        {
            "id": group_id,
            "name": f"Group {group_id}",
            "team_ids": sorted(team_ids),
        }
        for group_id, team_ids in sorted(groups.items())
    ]


def _build_teams(team_entries: dict[str, tuple[str, str, int]]) -> list[dict[str, object]]:
    return [
        {
            "id": team_id,
            "name": name,
            "group_id": group_id,
            "rating": rating,
        }
        for team_id, (name, group_id, rating) in sorted(team_entries.items())
    ]


def _build_fixtures(rows: list[tuple]) -> list[dict[str, object]]:
    fixtures: list[dict[str, object]] = []
    for match_id, stage, team_a, team_b, goals_a, goals_b, winner in rows:
        decided_by_penalties = goals_a == goals_b
        result: dict[str, object] = {
            "played": True,
            "team_a_goals": goals_a,
            "team_b_goals": goals_b,
        }
        if decided_by_penalties:
            result["decided_by_penalties"] = True
            if winner == team_a:
                result["penalty_team_a_goals"] = 4
                result["penalty_team_b_goals"] = 3
            else:
                result["penalty_team_a_goals"] = 3
                result["penalty_team_b_goals"] = 4
        fixture: dict[str, object] = {
            "id": match_id,
            "stage": stage,
            "team_a_id": team_a,
            "team_b_id": team_b,
            "result": result,
            "winner_team_id": winner,
        }
        fixtures.append(fixture)
    return fixtures


def write_dataset(year: str, payload: dict[str, object]) -> None:
    target = HISTORICAL_ROOT / f"wc{year}"
    target.mkdir(parents=True, exist_ok=True)
    teams = _build_teams(payload["teams"])  # type: ignore[arg-type]
    groups = _build_groups(payload["teams"])  # type: ignore[arg-type]
    fixtures = _build_fixtures(payload["fixtures"])  # type: ignore[arg-type]
    metadata = {
        "tournament": year,
        "name": payload["name"],
        "coverage_note": payload["coverage_note"],
    }
    (target / "teams.json").write_text(json.dumps(teams, indent=2) + "\n", encoding="utf-8")
    (target / "groups.json").write_text(json.dumps(groups, indent=2) + "\n", encoding="utf-8")
    (target / "fixtures.json").write_text(
        json.dumps(fixtures, indent=2) + "\n",
        encoding="utf-8",
    )
    (target / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {target} ({len(fixtures)} fixtures)")


def main() -> None:
    for year, payload in DATASETS.items():
        write_dataset(year, payload)


if __name__ == "__main__":
    main()

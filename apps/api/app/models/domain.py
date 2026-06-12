"""Domain models for tournament simulation."""

from pydantic import BaseModel, Field, model_validator


class Team(BaseModel):
    """A team participating in the tournament."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    group_id: str = Field(min_length=1)
    rating: float = Field(gt=0)


class MatchResult(BaseModel):
    """A played or simulated match score."""

    team_a_goals: int = Field(ge=0)
    team_b_goals: int = Field(ge=0)
    played: bool = True


class Match(BaseModel):
    """A tournament match."""

    id: str = Field(min_length=1)
    stage: str = Field(min_length=1)
    group_id: str | None = None
    team_a_id: str = Field(min_length=1)
    team_b_id: str = Field(min_length=1)
    result: MatchResult | None = None
    winner_team_id: str | None = None

    @model_validator(mode="after")
    def teams_must_be_distinct(self) -> "Match":
        if self.team_a_id == self.team_b_id:
            raise ValueError("match teams must be distinct")
        if self.winner_team_id is not None and self.winner_team_id not in {
            self.team_a_id,
            self.team_b_id,
        }:
            raise ValueError("winner_team_id must reference one of the match teams")
        return self


class Group(BaseModel):
    """A group of teams in the group stage."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    team_ids: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def team_ids_must_be_unique(self) -> "Group":
        if len(set(self.team_ids)) != len(self.team_ids):
            raise ValueError("group team_ids must be unique")
        if any(not team_id for team_id in self.team_ids):
            raise ValueError("group team_ids must be non-empty")
        return self


class GroupStandingRow(BaseModel):
    """A single team's row in a group table."""

    team_id: str = Field(min_length=1)
    played: int = Field(ge=0)
    wins: int = Field(ge=0)
    draws: int = Field(ge=0)
    losses: int = Field(ge=0)
    goals_for: int = Field(ge=0)
    goals_against: int = Field(ge=0)
    goal_difference: int
    points: int = Field(ge=0)

    @model_validator(mode="after")
    def totals_must_be_consistent(self) -> "GroupStandingRow":
        if self.played != self.wins + self.draws + self.losses:
            raise ValueError("played must equal wins + draws + losses")
        if self.goal_difference != self.goals_for - self.goals_against:
            raise ValueError("goal_difference must equal goals_for - goals_against")
        if self.points != (self.wins * 3) + self.draws:
            raise ValueError("points must equal wins * 3 + draws")
        return self


class TournamentConfig(BaseModel):
    """Tournament input data."""

    teams: list[Team] = Field(min_length=1)
    groups: list[Group] = Field(min_length=1)
    matches: list[Match] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_must_be_valid(self) -> "TournamentConfig":
        team_ids = {team.id for team in self.teams}
        group_ids = {group.id for group in self.groups}

        if len(team_ids) != len(self.teams):
            raise ValueError("team ids must be unique")
        if len(group_ids) != len(self.groups):
            raise ValueError("group ids must be unique")

        for group in self.groups:
            unknown_team_ids = set(group.team_ids) - team_ids
            if unknown_team_ids:
                raise ValueError("group references unknown team ids")

        for team in self.teams:
            if team.group_id not in group_ids:
                raise ValueError("team references unknown group_id")

        for match in self.matches:
            if match.team_a_id not in team_ids or match.team_b_id not in team_ids:
                raise ValueError("match references unknown team id")
            if match.group_id is not None and match.group_id not in group_ids:
                raise ValueError("match references unknown group_id")

        return self


class GroupStageResult(BaseModel):
    """Result of simulating the group stage."""

    simulated_matches: list[Match] = Field(default_factory=list)
    group_tables: dict[str, list[GroupStandingRow]] = Field(default_factory=dict)
    top_two_qualifiers: list[str] = Field(default_factory=list)
    third_place_rankings: list[GroupStandingRow] = Field(default_factory=list)
    third_place_qualifiers: list[str] = Field(default_factory=list)
    qualified_team_ids: list[str] = Field(default_factory=list)


class KnockoutResult(BaseModel):
    """Result of simulating the knockout stage."""

    rounds: dict[str, list[Match]] = Field(default_factory=dict)
    eliminated_stage_by_team: dict[str, str] = Field(default_factory=dict)
    finalists: list[str] = Field(default_factory=list)
    champion_team_id: str = Field(min_length=1)


class SimulationSummary(BaseModel):
    """Aggregated output from many tournament simulations."""

    stage_probabilities: dict[str, dict[str, float]] = Field(default_factory=dict)
    average_points_by_team: dict[str, float] = Field(default_factory=dict)
    group_qualification_probability: dict[str, float] = Field(default_factory=dict)
    top_two_probability: dict[str, float] = Field(default_factory=dict)
    third_place_finish_probability: dict[str, float] = Field(default_factory=dict)
    third_place_qualification_probability: dict[str, float] = Field(default_factory=dict)

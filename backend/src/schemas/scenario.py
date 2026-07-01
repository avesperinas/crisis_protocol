from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Resources(BaseModel):
    model_config = ConfigDict(extra="forbid")

    MIL: int = Field(ge=0)
    DIP: int = Field(ge=0)
    ECO: int = Field(ge=0)
    INT: int = Field(ge=0)


class Objective(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    evaluation_criteria: str


class Faction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    tagline: str
    description: str
    starting_resources: Resources
    token_budget_per_turn: int = Field(ge=3, le=6)
    public_objective: Objective
    hidden_objective: Objective
    available_actions_focus: list[str]
    evaluation_rubric: str


class CrisisCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str
    rule_modifier: str


class EventDef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    trigger_condition: str
    effect: str
    narrative_template: str


class PactTypeLabel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    help: str


class PactTypeLabels(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alliance: PactTypeLabel
    non_aggression: PactTypeLabel
    trade: PactTypeLabel
    intel_share: PactTypeLabel


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    year: str
    type: Literal["diplomatic", "economic", "hybrid"]
    max_turns: int = Field(ge=3, le=8)
    min_players: int = Field(ge=2)
    max_players: int = Field(le=8)
    context: str
    example_directive: str
    pact_type_labels: PactTypeLabels
    factions: list[Faction]
    crisis_cards: list[CrisisCard]
    event_pool: list[EventDef]

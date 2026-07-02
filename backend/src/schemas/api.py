"""Pydantic models for the REST API request/response envelope.

These are separate from src.models (ORM) and src.schemas.scenario (static data).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.scenario import PactTypeLabels

Posture = Literal["confrontational", "cooperative", "ambiguous"]


class TokenAllocationDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    MIL: int = Field(ge=0)
    DIP: int = Field(ge=0)
    ECO: int = Field(ge=0)
    INT: int = Field(ge=0)

    def total(self) -> int:
        return self.MIL + self.DIP + self.ECO + self.INT


class GameCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = "corinth_338"
    human_role_id: str  # e.g., "macedonia"
    mode: Literal["solo", "multiplayer"] = "solo"
    room_name: str | None = Field(default=None, max_length=40)
    async_mode: bool = False
    # Language for the whole game. If omitted, the creator's account locale is
    # used (falling back to Spanish). See Game.language.
    language: Literal["es", "en"] | None = None


class GameCreatedResponse(BaseModel):
    game_id: str
    your_role_id: str
    user_token: str
    join_code: str | None = None
    mode: str = "solo"


class GameJoin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    join_code: str
    role_id: str


class LobbySlot(BaseModel):
    role_id: str
    role_name: str
    tagline: str
    is_taken: bool
    is_human: bool


class LobbyStateView(BaseModel):
    game_id: str
    join_code: str
    room_name: str | None = None
    scenario_id: str
    scenario_name: str
    async_mode: bool = False
    slots: list[LobbySlot]
    is_started: bool
    is_host: bool
    connected_roles: list[str]


class FactionView(BaseModel):
    id: str
    name: str
    tagline: str
    public_objective: str


class PactView(BaseModel):
    id: str
    type: str
    player_a_id: str  # role_id
    player_b_id: str  # role_id
    is_secret: bool
    is_active: bool
    created_turn: int


class PostureSnapshot(BaseModel):
    role_id: str
    posture: Posture | None


class ScoreBreakdownView(BaseModel):
    objective: float
    efficiency: float
    capital: float
    decision_quality: float
    total: int


class ScoreboardEntry(BaseModel):
    role_id: str
    role_name: str
    is_human: bool
    score: ScoreBreakdownView
    public_objective_met: bool
    hidden_objective_met: bool
    public_objective_text: str
    hidden_objective_text: str


class PlayerView(BaseModel):
    """View of a single player from the perspective of the requesting human."""

    role_id: str
    role_name: str
    tagline: str
    is_ai: bool
    is_you: bool
    # Only populated for the requesting player:
    briefing: str | None = None
    resources: dict[str, int] | None = None  # private to the player
    token_budget_per_turn: int | None = None
    public_objective_text: str | None = None
    hidden_objective_text: str | None = None


class ResolvedActionView(BaseModel):
    role_id: str
    posture: Posture
    # Only show directive to the actor; for others, redacted.
    directive: str | None
    coherence_score: float | None
    decision_quality: float | None
    effective_multiplier: float | None
    action_type: str | None
    target_id: str | None


class TurnView(BaseModel):
    turn_number: int
    max_turns: int
    status: str  # collecting | resolving | finished
    tension_at_start: int
    tension_at_end: int | None
    narrative: str | None
    intel_for_you: str | None
    your_action_submitted: bool
    humans_submitted: int = 0
    humans_total: int = 0
    resolved_actions: list[ResolvedActionView] = []


class MessageView(BaseModel):
    id: str
    turn_number: int
    from_role_id: str
    to_role_id: str | None  # None = public
    content: str
    is_proposal: bool
    proposal_type: str | None
    proposal_status: str | None
    created_at: str  # ISO 8601


class GameStateView(BaseModel):
    """Everything the frontend needs to render the game page from the
    requesting player's perspective."""

    game_id: str
    scenario_id: str
    scenario_name: str
    status: str  # lobby | briefing | active | resolving | finished
    current_turn: int
    max_turns: int
    tension: int
    your_role_id: str
    example_directive: str
    pact_type_labels: PactTypeLabels
    factions: list[FactionView]  # public list of who's in the game
    you: PlayerView
    active_pacts: list[PactView] = []
    messages: list[MessageView] = []
    current_turn_view: TurnView | None = None
    previous_turn_view: TurnView | None = None


class PactProposalSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_role_id: str
    pact_type: Literal["alliance", "non_aggression", "trade", "intel_share"]
    is_secret: bool = False


class PactProposalResult(BaseModel):
    # "accepted"/"rejected" for bot targets (decided synchronously);
    # "pending" for human targets (they respond later).
    status: Literal["accepted", "rejected", "pending"]
    accepted: bool
    pact_id: str | None
    proposal_message_id: str
    reason: str


class PactProposalRespond(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accept: bool


class PactBreakResult(BaseModel):
    pact_id: str
    new_tension: int
    breaker_dip_after: int


class MessageSubmit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to_role_id: str | None = None  # None = public
    content: str = Field(min_length=1, max_length=500)


class ActionSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    posture: Posture
    tokens: TokenAllocationDTO
    directive: str = Field(min_length=1, max_length=300)


class ActionSubmittedResponse(BaseModel):
    accepted: bool
    turn_resolved: bool
    message: str = ""


class FinalResultView(BaseModel):
    game_id: str
    scenario_id: str
    scenario_name: str
    final_tension: int
    final_narrative: str | None = None
    scoreboard: list[ScoreboardEntry]

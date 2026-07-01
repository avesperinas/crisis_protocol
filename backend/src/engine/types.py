"""Pure dataclasses used by the deterministic engine.

The engine never touches SQLAlchemy. The DB layer (Phase 4) translates
between ORM models and these dataclasses so the engine remains trivially
unit-testable and decoupled from persistence.

Player identity inside the engine is the role_id (e.g. "macedonia"). This
is unique within a single game, which is all the engine cares about.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

Posture = Literal["confrontational", "cooperative", "ambiguous"]
Domain = Literal["MIL", "DIP", "ECO", "INT"]


class ActionType(str, Enum):
    MILITARY_OFFENSIVE = "military_offensive"
    MILITARY_DEFENSIVE = "military_defensive"
    DIPLOMATIC_PROPOSAL = "diplomatic_proposal"
    DIPLOMATIC_MEDIATION = "diplomatic_mediation"
    ECONOMIC_SANCTION = "economic_sanction"
    ECONOMIC_AID = "economic_aid"
    INTEL_ESPIONAGE = "intel_espionage"
    INTEL_COUNTER = "intel_counter"
    INFO_EXPOSE = "info_expose"
    PACT_BREAK = "pact_break"
    GENERIC = "generic"


class ThresholdEvent(str, Enum):
    GLOBAL_ACCORD_AVAILABLE = "global_accord_available"
    EMERGENCY_UNLOCKED = "emergency_unlocked"
    FINAL_TURN_TRIGGERED = "final_turn_triggered"
    CATASTROPHIC = "catastrophic"


@dataclass
class TokenAllocation:
    MIL: int = 0
    DIP: int = 0
    ECO: int = 0
    INT: int = 0

    def total(self) -> int:
        return self.MIL + self.DIP + self.ECO + self.INT

    def get(self, domain: Domain) -> int:
        return getattr(self, domain)


@dataclass
class ActionInput:
    """A player's sealed action for a single turn.

    `action_type` and `target_id` are explicit in Phase 2 (tests provide them).
    In Phase 3 they will be inferred by Claude from the directive.
    `coherence_multiplier` and `posture_modifier` default to no-op; Claude
    will populate them.
    """

    player_id: str  # role_id within the engine
    posture: Posture
    tokens: TokenAllocation
    directive: str
    action_type: ActionType
    target_id: str | None = None
    coherence_multiplier: float = 1.0
    posture_modifier: float = 0.0


@dataclass
class PlayerState:
    id: str  # role_id
    resources: dict[str, int]  # MIL/DIP/ECO/INT pool
    is_ai: bool = True


@dataclass
class PactState:
    id: str
    type: str  # alliance | non_aggression | trade | intel_share | mediation
    player_a_id: str  # role_id
    player_b_id: str  # role_id
    is_active: bool = True
    is_secret: bool = False
    created_turn: int = 0
    broken_turn: int | None = None
    broken_by_player_id: str | None = None
    terms: dict | None = None


@dataclass
class GameState:
    game_id: str
    scenario_id: str
    turn_number: int
    tension: int
    players: list[PlayerState]
    pacts: list[PactState]
    max_turns: int

    def get_player(self, role_id: str) -> PlayerState:
        for p in self.players:
            if p.id == role_id:
                return p
        raise KeyError(f"Unknown player: {role_id!r}")

    def active_pacts_for(self, role_id: str) -> list[PactState]:
        return [
            p for p in self.pacts
            if p.is_active and role_id in (p.player_a_id, p.player_b_id)
        ]

    def has_pact_between(self, a: str, b: str, type_: str | None = None) -> bool:
        for p in self.pacts:
            if not p.is_active:
                continue
            pair = {p.player_a_id, p.player_b_id}
            if pair == {a, b} and (type_ is None or p.type == type_):
                return True
        return False


@dataclass
class TurnRecord:
    """A snapshot of one resolved turn, used by GameHistory for scoring."""

    turn_number: int
    actions: list[ActionInput]
    tension_at_start: int
    tension_at_end: int


@dataclass
class GameHistory:
    """Everything an objective-evaluator may need to look at."""

    state: GameState  # final state at evaluation time
    turns: list[TurnRecord]
    initial_resources: dict[str, dict[str, int]]
    exposed_pacts: set[str] = field(default_factory=set)


@dataclass
class ActionEffects:
    """Raw or final delta produced by a single action."""

    tension_delta: int = 0
    # role_id -> domain -> delta (negative = loss, positive = gain)
    resource_changes: dict[str, dict[str, int]] = field(default_factory=dict)
    espionage_revealed: bool = False
    info_revealed: list[dict] = field(default_factory=list)

    def add_resource_change(self, role_id: str, domain: str, delta: int) -> None:
        if role_id not in self.resource_changes:
            self.resource_changes[role_id] = {}
        self.resource_changes[role_id][domain] = (
            self.resource_changes[role_id].get(domain, 0) + delta
        )


@dataclass
class ResolvedAction:
    action: ActionInput
    base_effects: ActionEffects
    final_effects: ActionEffects
    interaction_notes: list[str] = field(default_factory=list)


@dataclass
class TurnResult:
    """Output of resolve_turn. Pure; the caller persists if needed."""

    resolved_actions: list[ResolvedAction]
    final_tension: int
    threshold_events: list[ThresholdEvent]
    final_player_resources: dict[str, dict[str, int]]
    log: list[str] = field(default_factory=list)

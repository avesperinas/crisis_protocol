"""Builders for engine tests: keeps each test concise."""

from src.engine.types import (
    ActionInput,
    ActionType,
    GameState,
    PactState,
    PlayerState,
    Posture,
    TokenAllocation,
)


def make_player(role_id: str, **resources: int) -> PlayerState:
    defaults = {"MIL": 10, "DIP": 10, "ECO": 10, "INT": 10}
    defaults.update(resources)
    return PlayerState(id=role_id, resources=defaults)


def make_state(
    *players: PlayerState,
    tension: int = 50,
    pacts: list[PactState] | None = None,
    turn_number: int = 1,
    max_turns: int = 4,
    scenario_id: str = "corinth_338",
) -> GameState:
    return GameState(
        game_id="test-game",
        scenario_id=scenario_id,
        turn_number=turn_number,
        tension=tension,
        players=list(players),
        pacts=pacts or [],
        max_turns=max_turns,
    )


def make_action(
    player_id: str,
    action_type: ActionType,
    target_id: str | None = None,
    posture: Posture = "ambiguous",
    mil: int = 0,
    dip: int = 0,
    eco: int = 0,
    intel: int = 0,
    directive: str = "test directive",
    coherence: float = 1.0,
) -> ActionInput:
    return ActionInput(
        player_id=player_id,
        posture=posture,
        tokens=TokenAllocation(MIL=mil, DIP=dip, ECO=eco, INT=intel),
        directive=directive,
        action_type=action_type,
        target_id=target_id,
        coherence_multiplier=coherence,
    )


def make_pact(
    a: str,
    b: str,
    pact_type: str,
    is_active: bool = True,
    is_secret: bool = False,
    created_turn: int = 1,
    broken_turn: int | None = None,
    broken_by: str | None = None,
    terms: dict | None = None,
    id_: str | None = None,
) -> PactState:
    return PactState(
        id=id_ or f"{a}-{b}-{pact_type}",
        type=pact_type,
        player_a_id=a,
        player_b_id=b,
        is_active=is_active,
        is_secret=is_secret,
        created_turn=created_turn,
        broken_turn=broken_turn,
        broken_by_player_id=broken_by,
        terms=terms,
    )

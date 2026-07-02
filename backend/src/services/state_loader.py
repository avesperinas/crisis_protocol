"""Translate between SQLAlchemy ORM and the pure engine dataclasses.

The engine uses role_id as the player identity. The DB uses UUID. This module
hides the mapping: callers pass game_id and get back engine-friendly types.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.engine.types import (
    ActionInput,
    ActionType,
    GameHistory,
    GameState,
    PactState,
    PlayerState,
    TokenAllocation,
    TurnRecord,
)
from src.models import Action, Game, Pact, Player, Turn


async def load_game_state(session: AsyncSession, game_id: str) -> GameState:
    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one()
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    pacts = (
        (await session.execute(select(Pact).where(Pact.game_id == game_id))).scalars().all()
    )

    player_states = [
        PlayerState(
            id=p.role_id,
            resources=dict(p.resources),
            is_ai=p.is_ai,
            credibility=p.credibility,
        )
        for p in players
    ]
    pact_states = [
        PactState(
            id=p.id,
            type=p.type,
            player_a_id=_role_id_for(p.player_a_id, players),
            player_b_id=_role_id_for(p.player_b_id, players),
            is_active=p.is_active,
            is_secret=p.is_secret,
            created_turn=p.created_turn,
            broken_turn=p.broken_turn,
            broken_by_player_id=(
                _role_id_for(p.broken_by_player_id, players)
                if p.broken_by_player_id
                else None
            ),
            terms=p.terms,
        )
        for p in pacts
    ]

    return GameState(
        game_id=game.id,
        scenario_id=game.scenario_id,
        turn_number=game.current_turn,
        tension=game.tension,
        players=player_states,
        pacts=pact_states,
        max_turns=game.max_turns,
    )


async def load_game_history(session: AsyncSession, game_id: str) -> GameHistory:
    state = await load_game_state(session, game_id)

    turns = (
        (
            await session.execute(
                select(Turn).where(Turn.game_id == game_id).order_by(Turn.turn_number)
            )
        )
        .scalars()
        .all()
    )
    actions = (
        (
            await session.execute(
                select(Action)
                .join(Turn, Action.turn_id == Turn.id)
                .where(Turn.game_id == game_id)
            )
        )
        .scalars()
        .all()
    )
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )

    actions_by_turn: dict[str, list[Action]] = {}
    for a in actions:
        actions_by_turn.setdefault(a.turn_id, []).append(a)

    turn_records: list[TurnRecord] = []
    for t in turns:
        action_inputs: list[ActionInput] = []
        for a in actions_by_turn.get(t.id, []):
            role_id = _role_id_for(a.player_id, players)
            target_role = _role_id_for_optional(
                (a.effects or {}).get("target_id"), players
            ) if a.effects else None
            action_inputs.append(
                ActionInput(
                    player_id=role_id,
                    posture=a.posture,  # type: ignore[arg-type]
                    tokens=TokenAllocation(
                        MIL=a.tokens_mil, DIP=a.tokens_dip, ECO=a.tokens_eco, INT=a.tokens_int
                    ),
                    directive=a.directive,
                    action_type=_safe_action_type((a.effects or {}).get("action_type")),
                    target_id=target_role,
                    coherence_multiplier=a.effective_multiplier or 1.0,
                )
            )
        turn_records.append(
            TurnRecord(
                turn_number=t.turn_number,
                actions=action_inputs,
                tension_at_start=t.tension_at_start,
                tension_at_end=t.tension_at_end or t.tension_at_start,
            )
        )

    # Initial resources are reconstructed from the scenario data via the player rows
    # we have right now — the engine reads them from history.initial_resources only
    # for scoring. For PoC we stash the scenario's starting_resources on the first
    # snapshot when the game is created; here we look up from scenarios.
    from src.scenarios import get_scenario

    scenario = get_scenario(state.scenario_id)
    initial_resources = {
        f.id: {
            "MIL": f.starting_resources.MIL,
            "DIP": f.starting_resources.DIP,
            "ECO": f.starting_resources.ECO,
            "INT": f.starting_resources.INT,
        }
        for f in scenario.factions
    }

    return GameHistory(
        state=state,
        turns=turn_records,
        initial_resources=initial_resources,
        exposed_pacts=set(),
    )


def _role_id_for(player_uuid: str, players: list[Player]) -> str:
    for p in players:
        if p.id == player_uuid:
            return p.role_id
    raise KeyError(f"No player found with uuid {player_uuid!r}")


def _role_id_for_optional(player_uuid: str | None, players: list[Player]) -> str | None:
    if not player_uuid:
        return None
    for p in players:
        if p.id == player_uuid:
            return p.role_id
    return None


def _safe_action_type(value: str | None) -> ActionType:
    if not value:
        return ActionType.GENERIC
    try:
        return ActionType(value)
    except ValueError:
        return ActionType.GENERIC

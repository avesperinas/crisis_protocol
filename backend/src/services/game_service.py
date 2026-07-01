"""Game lifecycle: creation, joining, starting, and briefing pregeneration."""

import asyncio
import logging
import random
import string
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Game, GameStatus, Player, Turn, TurnStatus
from src.scenarios import get_scenario
from src.services.ai_service import AIService

logger = logging.getLogger("crisis.game")

ASYNC_TURN_TIMEOUT_SECONDS = 86400  # 24h — async mode lets players act whenever they can


class GameServiceError(ValueError):
    pass


def _generate_join_code() -> str:
    chars = (string.ascii_uppercase + string.digits).translate(str.maketrans("", "", "OI01"))
    return "".join(random.choices(chars, k=6))


async def create_game(
    session: AsyncSession,
    *,
    scenario_id: str,
    human_role_id: str,
    mode: str = "solo",
    account_id: str | None = None,
    room_name: str | None = None,
    async_mode: bool = False,
) -> tuple[Game, Player]:
    """Create a Game + players.

    solo mode: all faction slots are filled immediately (human + bots), Turn 1 starts.
    multiplayer mode: only the host slot is created; game stays in LOBBY until start_game() is called.

    account_id: if the creator is authenticated, Player.user_id is set to their real
    account id (enables future stats/history). Guests get a throwaway UUID.
    """
    scenario = get_scenario(scenario_id)
    faction_ids = {f.id for f in scenario.factions}
    if human_role_id not in faction_ids:
        raise GameServiceError(f"role {human_role_id!r} is not in scenario {scenario_id!r}")

    join_code = _generate_join_code() if mode == "multiplayer" else None
    game = Game(
        scenario_id=scenario_id,
        max_turns=scenario.max_turns,
        status=GameStatus.ACTIVE.value if mode == "solo" else GameStatus.LOBBY.value,
        current_turn=1 if mode == "solo" else 0,
        tension=50,
        mode=mode,
        join_code=join_code,
        host_role_id=human_role_id,
        room_name=(room_name or "").strip()[:40] or None if mode == "multiplayer" else None,
        turn_timeout_seconds=ASYNC_TURN_TIMEOUT_SECONDS if (mode == "multiplayer" and async_mode) else None,
    )
    session.add(game)
    await session.flush()

    human_player: Player | None = None

    if mode == "solo":
        for faction in scenario.factions:
            is_human = faction.id == human_role_id
            res = faction.starting_resources
            player = Player(
                game_id=game.id,
                role_id=faction.id,
                is_ai=not is_human,
                user_id=(account_id or str(uuid.uuid4())) if is_human else None,
                resources={"MIL": res.MIL, "DIP": res.DIP, "ECO": res.ECO, "INT": res.INT},
            )
            session.add(player)
            if is_human:
                human_player = player
        turn1 = Turn(
            game_id=game.id,
            turn_number=1,
            status=TurnStatus.COLLECTING.value,
            tension_at_start=game.tension,
        )
        session.add(turn1)
    else:
        # Multiplayer: only the host joins now; others join via join_code.
        host_faction = next(f for f in scenario.factions if f.id == human_role_id)
        res = host_faction.starting_resources
        human_player = Player(
            game_id=game.id,
            role_id=human_role_id,
            is_ai=False,
            user_id=account_id or str(uuid.uuid4()),
            resources={"MIL": res.MIL, "DIP": res.DIP, "ECO": res.ECO, "INT": res.INT},
        )
        session.add(human_player)

    await session.commit()
    await session.refresh(game)
    assert human_player is not None
    return game, human_player


async def join_game(
    session: AsyncSession,
    *,
    join_code: str,
    role_id: str,
    account_id: str | None = None,
) -> tuple[Game, Player]:
    """Claim a faction slot in a lobby game by join code."""
    game = (
        await session.execute(select(Game).where(Game.join_code == join_code.upper()))
    ).scalar_one_or_none()
    if not game:
        raise GameServiceError(f"no game with join code {join_code!r}")
    if game.status != GameStatus.LOBBY.value:
        raise GameServiceError("game has already started or finished")

    scenario = get_scenario(game.scenario_id)
    if role_id not in {f.id for f in scenario.factions}:
        raise GameServiceError(f"role {role_id!r} not in scenario {game.scenario_id!r}")

    existing = (
        (await session.execute(select(Player).where(Player.game_id == game.id))).scalars().all()
    )
    if any(p.role_id == role_id for p in existing):
        raise GameServiceError(f"role {role_id!r} is already taken")

    faction = next(f for f in scenario.factions if f.id == role_id)
    res = faction.starting_resources
    player = Player(
        game_id=game.id,
        role_id=role_id,
        is_ai=False,
        user_id=account_id or str(uuid.uuid4()),
        resources={"MIL": res.MIL, "DIP": res.DIP, "ECO": res.ECO, "INT": res.INT},
    )
    session.add(player)
    await session.commit()
    return game, player


async def start_game(
    session: AsyncSession,
    *,
    ai_service: AIService,
    game_id: str,
    requester_role_id: str,
) -> None:
    """Transition a lobby game to active: fill remaining slots with bots, create Turn 1."""
    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one_or_none()
    if not game:
        raise GameServiceError("game not found")
    if game.status != GameStatus.LOBBY.value:
        raise GameServiceError("game is not in lobby state")
    if game.host_role_id != requester_role_id:
        raise GameServiceError("only the host can start the game")

    scenario = get_scenario(game.scenario_id)
    existing = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    taken_roles = {p.role_id for p in existing}

    for faction in scenario.factions:
        if faction.id not in taken_roles:
            res = faction.starting_resources
            session.add(Player(
                game_id=game.id,
                role_id=faction.id,
                is_ai=True,
                user_id=None,
                resources={"MIL": res.MIL, "DIP": res.DIP, "ECO": res.ECO, "INT": res.INT},
            ))

    game.status = GameStatus.ACTIVE.value
    game.current_turn = 1
    session.add(Turn(
        game_id=game.id,
        turn_number=1,
        status=TurnStatus.COLLECTING.value,
        tension_at_start=game.tension,
    ))
    await session.commit()
    await pregenerate_briefings(session, ai_service=ai_service, game_id=game_id)

    from src.config import settings
    from src.services.turn_service import _auto_submit_timeout

    timeout_seconds = (
        game.turn_timeout_seconds if game.turn_timeout_seconds is not None else settings.turn_timeout_seconds
    )
    if timeout_seconds > 0:
        asyncio.create_task(_auto_submit_timeout(game_id, 1, timeout_seconds))


async def pregenerate_briefings(
    session: AsyncSession, *, ai_service: AIService, game_id: str
) -> None:
    """Generate a briefing for every player that doesn't have one yet. Errors are logged and skipped."""
    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one()
    scenario = get_scenario(game.scenario_id)
    factions_by_id = {f.id: f for f in scenario.factions}
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    targets = [p for p in players if not p.briefing]
    if not targets:
        return

    async def _gen(player: Player) -> tuple[Player, str | None]:
        try:
            text = await ai_service.generate_briefing(scenario, factions_by_id[player.role_id])
            return player, text
        except Exception as e:  # noqa: BLE001
            logger.warning("Briefing pregen failed for %s: %s", player.role_id, e)
            return player, None

    results = await asyncio.gather(*(_gen(p) for p in targets))
    for player, text in results:
        if text:
            player.briefing = text
    await session.commit()

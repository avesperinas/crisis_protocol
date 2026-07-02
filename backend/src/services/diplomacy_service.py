"""Bot diplomacy (Phase B of v2): bots answer messages and open negotiations.

Two entry points, each with a directly-testable core and a fire-and-forget
scheduler that opens its own DB session (mirroring _auto_submit_timeout):

- generate_bot_reply / schedule_bot_reply — when a human sends a private
  message to a bot, the bot answers in character.
- run_bot_diplomacy_for_game / schedule_bot_diplomacy — when a new turn opens,
  each bot may make one diplomatic move: a public statement, a private message
  or a pact proposal (bot→human proposals stay pending; bot→bot resolve
  immediately through the usual pact-response call).
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Action, Game, GameStatus, Message, Player, Turn, TurnStatus
from src.scenarios import get_scenario
from src.services.ai_service import AIService
from src.services.chronicle import (
    build_chronicle,
    credibility_summary,
    format_message_lines,
    load_turn_messages,
    pacts_summary_for_viewer,
    visible_to,
)

logger = logging.getLogger("crisis.diplomacy")

_MESSAGE_MAX = 500


# ---------- bot replies to private messages ----------


async def generate_bot_reply(
    session: AsyncSession,
    *,
    ai_service: AIService,
    game_id: str,
    message_id: str,
) -> Message | None:
    """Generate and persist a bot's in-character reply to a private message.
    Returns the reply Message, or None when no reply applies (wrong recipient,
    game inactive, Claude failure — silence over canned text).
    """
    game = (
        await session.execute(select(Game).where(Game.id == game_id))
    ).scalar_one_or_none()
    if not game or game.status != GameStatus.ACTIVE.value:
        return None

    incoming = (
        await session.execute(
            select(Message)
            .join(Turn, Message.turn_id == Turn.id)
            .where(Message.id == message_id, Turn.game_id == game_id)
        )
    ).scalar_one_or_none()
    if not incoming or incoming.to_player_id is None or incoming.is_proposal:
        return None

    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    by_uuid = {p.id: p for p in players}
    role_by_uuid = {p.id: p.role_id for p in players}
    sender = by_uuid.get(incoming.from_player_id)
    recipient = by_uuid.get(incoming.to_player_id)
    if not sender or not recipient or not recipient.is_ai or sender.is_ai:
        return None

    scenario = get_scenario(game.scenario_id, game.language)
    factions_by_id = {f.id: f for f in scenario.factions}
    bot_faction = factions_by_id[recipient.role_id]
    sender_faction = factions_by_id[sender.role_id]

    chronicle = await build_chronicle(
        session,
        game_id=game_id,
        up_to_turn_number=game.current_turn,
        role_by_uuid=role_by_uuid,
    )
    thread_block = await _private_thread(
        session, game_id, sender.id, recipient.id, role_by_uuid, exclude_id=incoming.id
    )
    active_pacts = await _active_pacts(session, game_id)

    reply_text = await ai_service.reply_to_message(
        scenario=scenario,
        faction=bot_faction,
        briefing=recipient.briefing or "(no briefing available)",
        sender_id=sender.role_id,
        sender_name=sender_faction.name,
        incoming=incoming.content,
        turn_number=game.current_turn,
        max_turns=game.max_turns,
        tension=game.tension,
        pacts_summary=pacts_summary_for_viewer(active_pacts, role_by_uuid, recipient.id),
        chronicle=chronicle,
        thread_block=thread_block,
        language=game.language,
    )
    if not reply_text:
        return None

    current_turn = (
        await session.execute(
            select(Turn).where(Turn.game_id == game_id, Turn.turn_number == game.current_turn)
        )
    ).scalar_one_or_none()
    if not current_turn:
        return None

    reply = Message(
        turn_id=current_turn.id,
        from_player_id=recipient.id,
        to_player_id=sender.id,
        content=reply_text[:_MESSAGE_MAX],
    )
    session.add(reply)
    await session.commit()

    from src.services.connection_manager import manager

    await manager.broadcast(
        game_id,
        {"type": "message_received", "from_role_id": recipient.role_id, "to_role_id": sender.role_id},
    )
    return reply


def schedule_bot_reply(game_id: str, message_id: str) -> None:
    """Fire-and-forget wrapper: replies never block or fail the sender's request."""

    async def _task() -> None:
        from src.api.deps import get_ai_service
        from src.db import async_session

        try:
            async with async_session() as session:
                await generate_bot_reply(
                    session,
                    ai_service=get_ai_service(),
                    game_id=game_id,
                    message_id=message_id,
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Bot reply task failed (game %s, msg %s): %s", game_id, message_id, e)

    asyncio.create_task(_task())


# ---------- bot-initiated diplomacy at turn start ----------


async def run_bot_diplomacy_for_game(
    session: AsyncSession,
    *,
    ai_service: AIService,
    game_id: str,
    turn_number: int,
) -> int:
    """Give every bot one optional diplomatic move at the start of a turn.
    Returns the number of moves actually made. Runs bots sequentially so a
    pact signed by an earlier bot is visible to later ones.
    """
    game = (
        await session.execute(select(Game).where(Game.id == game_id))
    ).scalar_one_or_none()
    if (
        not game
        or game.status != GameStatus.ACTIVE.value
        or game.current_turn != turn_number
    ):
        return 0
    turn = (
        await session.execute(
            select(Turn).where(Turn.game_id == game_id, Turn.turn_number == turn_number)
        )
    ).scalar_one_or_none()
    if not turn or turn.status != TurnStatus.COLLECTING.value:
        return 0

    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    players_by_role = {p.role_id: p for p in players}
    role_by_uuid = {p.id: p.role_id for p in players}
    scenario = get_scenario(game.scenario_id, game.language)
    factions_by_id = {f.id: f for f in scenario.factions}

    chronicle = await build_chronicle(
        session, game_id=game_id, up_to_turn_number=turn_number, role_by_uuid=role_by_uuid
    )
    prev_messages = await _previous_turn_messages(session, game_id, turn_number)
    intel_by_role = await _previous_intel(session, game_id, turn_number, role_by_uuid)
    credibility_block = credibility_summary(players_by_role)

    moves = 0
    for role, player in players_by_role.items():
        if not player.is_ai or not player.briefing:
            continue
        faction = factions_by_id[role]
        active_pacts = await _active_pacts(session, game_id)
        factions_list = ", ".join(
            f"{f.id} — {f.name}" for f in scenario.factions if f.id != role
        )
        decision = await ai_service.decide_bot_diplomacy(
            scenario=scenario,
            faction=faction,
            briefing=player.briefing,
            turn_number=turn_number,
            max_turns=game.max_turns,
            tension=game.tension,
            resources=dict(player.resources),
            factions_list=factions_list,
            pacts_summary=pacts_summary_for_viewer(active_pacts, role_by_uuid, player.id),
            chronicle=chronicle,
            messages_block=format_message_lines(
                visible_to(prev_messages, player.id), role_by_uuid
            ),
            credibility_block=credibility_block,
            previous_intel=intel_by_role.get(role, "(no previous report)"),
            language=game.language,
        )
        if decision is None or decision.action == "none":
            continue

        if decision.action == "message_public":
            session.add(
                Message(
                    turn_id=turn.id,
                    from_player_id=player.id,
                    to_player_id=None,
                    content=decision.content[:_MESSAGE_MAX],
                )
            )
            await session.commit()
            moves += 1
        elif decision.action == "message_private":
            target = players_by_role.get(decision.target_id or "")
            if not target or target.id == player.id:
                continue
            session.add(
                Message(
                    turn_id=turn.id,
                    from_player_id=player.id,
                    to_player_id=target.id,
                    content=decision.content[:_MESSAGE_MAX],
                )
            )
            await session.commit()
            moves += 1
        elif decision.action == "propose_pact":
            target = players_by_role.get(decision.target_id or "")
            if not target or target.id == player.id:
                continue
            from src.services.pact_service import PactServiceError, propose_pact

            try:
                await propose_pact(
                    session,
                    ai_service=ai_service,
                    game_id=game_id,
                    proposer_role_id=role,
                    target_role_id=target.role_id,
                    pact_type=decision.pact_type,  # type: ignore[arg-type]
                    is_secret=decision.is_secret,
                )
                moves += 1
            except PactServiceError as e:
                logger.info("Bot %s pact proposal skipped: %s", role, e)
        logger.info(
            "Bot diplomacy: %s turn %d action=%s target=%s",
            role, turn_number, decision.action, decision.target_id,
        )

    if moves:
        from src.services.connection_manager import manager

        await manager.broadcast(game_id, {"type": "message_received"})
    return moves


def schedule_bot_diplomacy(game_id: str, turn_number: int) -> None:
    """Fire-and-forget wrapper for turn resolution to call."""

    async def _task() -> None:
        from src.api.deps import get_ai_service
        from src.db import async_session

        try:
            async with async_session() as session:
                await run_bot_diplomacy_for_game(
                    session,
                    ai_service=get_ai_service(),
                    game_id=game_id,
                    turn_number=turn_number,
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "Bot diplomacy task failed (game %s, turn %d): %s", game_id, turn_number, e
            )

    asyncio.create_task(_task())


# ---------- helpers ----------


async def _active_pacts(session: AsyncSession, game_id: str):
    from src.models import Pact

    return (
        (
            await session.execute(
                select(Pact).where(Pact.game_id == game_id, Pact.is_active == True)  # noqa: E712
            )
        )
        .scalars()
        .all()
    )


async def _private_thread(
    session: AsyncSession,
    game_id: str,
    a_uuid: str,
    b_uuid: str,
    role_by_uuid: dict[str, str],
    *,
    exclude_id: str | None = None,
) -> str:
    from sqlalchemy import and_, or_

    messages = (
        (
            await session.execute(
                select(Message)
                .join(Turn, Message.turn_id == Turn.id)
                .where(
                    Turn.game_id == game_id,
                    or_(
                        and_(Message.from_player_id == a_uuid, Message.to_player_id == b_uuid),
                        and_(Message.from_player_id == b_uuid, Message.to_player_id == a_uuid),
                    ),
                )
                .order_by(Message.created_at.asc())
            )
        )
        .scalars()
        .all()
    )
    remaining = [m for m in messages if m.id != exclude_id]
    if not remaining:
        return "(no previous messages)"
    return format_message_lines(remaining, role_by_uuid)


async def _previous_turn_messages(
    session: AsyncSession, game_id: str, current_turn_number: int
) -> list[Message]:
    if current_turn_number <= 1:
        return []
    prev_turn = (
        await session.execute(
            select(Turn).where(
                Turn.game_id == game_id, Turn.turn_number == current_turn_number - 1
            )
        )
    ).scalar_one_or_none()
    if not prev_turn:
        return []
    return await load_turn_messages(session, turn_id=prev_turn.id)


async def _previous_intel(
    session: AsyncSession,
    game_id: str,
    current_turn_number: int,
    role_by_uuid: dict[str, str],
) -> dict[str, str]:
    if current_turn_number <= 1:
        return {}
    prev_turn = (
        await session.execute(
            select(Turn).where(
                Turn.game_id == game_id, Turn.turn_number == current_turn_number - 1
            )
        )
    ).scalar_one_or_none()
    if not prev_turn:
        return {}
    actions = (
        (await session.execute(select(Action).where(Action.turn_id == prev_turn.id)))
        .scalars()
        .all()
    )
    return {
        role_by_uuid[a.player_id]: a.intel_report
        for a in actions
        if a.player_id in role_by_uuid and a.intel_report
    }

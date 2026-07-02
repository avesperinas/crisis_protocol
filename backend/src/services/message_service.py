"""Message lifecycle.

Visibility rules:
- to_player_id is null → public, all see it.
- to_player_id set → only sender and recipient see it.
- Proposal messages (is_proposal=True) follow the same rule.

Since Phase B, a private message from a human to a bot triggers an
in-character bot reply, generated in the background (diplomacy_service).
"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Game, Message, Player, Turn


class MessageServiceError(ValueError):
    pass


async def send_message(
    session: AsyncSession,
    *,
    game_id: str,
    from_role_id: str,
    to_role_id: str | None,
    content: str,
    trigger_bot_reply: bool = True,
) -> Message:
    if not content.strip():
        raise MessageServiceError("content must not be empty")
    if len(content) > 500:
        raise MessageServiceError("content must be ≤ 500 chars")

    game = (await session.execute(select(Game).where(Game.id == game_id))).scalar_one_or_none()
    if not game:
        raise MessageServiceError("game not found")
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    players_by_role = {p.role_id: p for p in players}
    if from_role_id not in players_by_role:
        raise MessageServiceError(f"unknown sender {from_role_id!r}")
    sender = players_by_role[from_role_id]

    to_player_uuid: str | None = None
    if to_role_id is not None:
        if to_role_id not in players_by_role:
            raise MessageServiceError(f"unknown recipient {to_role_id!r}")
        if to_role_id == from_role_id:
            raise MessageServiceError("cannot send to yourself")
        to_player_uuid = players_by_role[to_role_id].id

    current_turn = (
        await session.execute(
            select(Turn)
            .where(Turn.game_id == game_id, Turn.turn_number == game.current_turn)
        )
    ).scalar_one()
    message = Message(
        turn_id=current_turn.id,
        from_player_id=sender.id,
        to_player_id=to_player_uuid,
        content=content,
        is_proposal=False,
    )
    session.add(message)
    await session.commit()

    from src.services.connection_manager import manager

    await manager.broadcast(
        game_id,
        {"type": "message_received", "from_role_id": from_role_id, "to_role_id": to_role_id},
    )

    # A human writing privately to a bot gets an in-character reply, generated
    # in the background so the sender's request never blocks on Claude.
    if (
        trigger_bot_reply
        and not sender.is_ai
        and to_role_id is not None
        and players_by_role[to_role_id].is_ai
    ):
        from src.services.diplomacy_service import schedule_bot_reply

        schedule_bot_reply(game_id, message.id)
    return message


async def list_visible_messages(
    session: AsyncSession, *, game_id: str, viewer_role_id: str
) -> list[Message]:
    """Return all messages in the game that the viewer is allowed to see, ordered
    oldest-first by created_at."""
    players = (
        (await session.execute(select(Player).where(Player.game_id == game_id))).scalars().all()
    )
    players_by_role = {p.role_id: p for p in players}
    if viewer_role_id not in players_by_role:
        raise MessageServiceError(f"unknown viewer {viewer_role_id!r}")
    viewer = players_by_role[viewer_role_id]

    # Join on turn so we filter by game.
    rows = (
        (
            await session.execute(
                select(Message)
                .join(Turn, Message.turn_id == Turn.id)
                .where(
                    Turn.game_id == game_id,
                    or_(
                        Message.to_player_id.is_(None),  # public
                        Message.from_player_id == viewer.id,
                        Message.to_player_id == viewer.id,
                    ),
                )
                .order_by(Message.created_at.asc())
            )
        )
        .scalars()
        .all()
    )
    return list(rows)

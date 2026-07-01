"""Friend search, requests, and pull-based room invites (no push notifications)."""

from dataclasses import dataclass

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Friendship, FriendshipStatus, Game, RoomInvite, User


class FriendServiceError(ValueError):
    pass


@dataclass
class FriendEntry:
    friendship_id: str
    user_id: str
    username: str
    status: str
    direction: str  # "incoming" | "outgoing" | "mutual"


@dataclass
class InviteEntry:
    id: str
    from_username: str
    game_id: str
    join_code: str
    room_name: str | None
    scenario_name: str


async def search_users(
    session: AsyncSession, *, query: str, exclude_user_id: str, limit: int = 10
) -> list[User]:
    query = query.strip()
    if not query:
        return []
    rows = (
        await session.execute(
            select(User)
            .where(User.username.ilike(f"%{query}%"), User.id != exclude_user_id)
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)


async def _get_friendship_between(
    session: AsyncSession, user_a: str, user_b: str
) -> Friendship | None:
    return (
        await session.execute(
            select(Friendship).where(
                or_(
                    and_(Friendship.requester_id == user_a, Friendship.recipient_id == user_b),
                    and_(Friendship.requester_id == user_b, Friendship.recipient_id == user_a),
                )
            )
        )
    ).scalar_one_or_none()


async def send_friend_request(
    session: AsyncSession, *, requester_id: str, recipient_username: str
) -> Friendship:
    recipient = (
        await session.execute(select(User).where(User.username == recipient_username.strip()))
    ).scalar_one_or_none()
    if not recipient:
        raise FriendServiceError(f"user {recipient_username!r} not found")
    if recipient.id == requester_id:
        raise FriendServiceError("cannot friend yourself")

    existing = await _get_friendship_between(session, requester_id, recipient.id)
    if existing:
        raise FriendServiceError("a friendship or request already exists with this user")

    friendship = Friendship(requester_id=requester_id, recipient_id=recipient.id)
    session.add(friendship)
    await session.commit()
    return friendship


async def accept_friend_request(session: AsyncSession, *, user_id: str, friendship_id: str) -> None:
    friendship = (
        await session.execute(select(Friendship).where(Friendship.id == friendship_id))
    ).scalar_one_or_none()
    if not friendship:
        raise FriendServiceError("friend request not found")
    if friendship.recipient_id != user_id:
        raise FriendServiceError("only the recipient can accept this request")
    friendship.status = FriendshipStatus.ACCEPTED.value
    await session.commit()


async def remove_friendship(session: AsyncSession, *, user_id: str, friendship_id: str) -> None:
    """Declines a pending request or removes an existing friendship — either party may do this."""
    friendship = (
        await session.execute(select(Friendship).where(Friendship.id == friendship_id))
    ).scalar_one_or_none()
    if not friendship:
        raise FriendServiceError("friendship not found")
    if user_id not in (friendship.requester_id, friendship.recipient_id):
        raise FriendServiceError("not a party to this friendship")
    await session.delete(friendship)
    await session.commit()


async def list_friendships(session: AsyncSession, *, user_id: str) -> list[FriendEntry]:
    rows = (
        await session.execute(
            select(Friendship).where(
                or_(Friendship.requester_id == user_id, Friendship.recipient_id == user_id)
            )
        )
    ).scalars().all()
    if not rows:
        return []

    other_ids = {
        (f.recipient_id if f.requester_id == user_id else f.requester_id) for f in rows
    }
    users = (
        await session.execute(select(User).where(User.id.in_(other_ids)))
    ).scalars().all()
    username_by_id = {u.id: u.username for u in users}

    entries: list[FriendEntry] = []
    for f in rows:
        is_requester = f.requester_id == user_id
        other_id = f.recipient_id if is_requester else f.requester_id
        if f.status == FriendshipStatus.ACCEPTED.value:
            direction = "mutual"
        else:
            direction = "outgoing" if is_requester else "incoming"
        entries.append(
            FriendEntry(
                friendship_id=f.id,
                user_id=other_id,
                username=username_by_id.get(other_id, "?"),
                status=f.status,
                direction=direction,
            )
        )
    return entries


async def _are_friends(session: AsyncSession, user_a: str, user_b: str) -> bool:
    f = await _get_friendship_between(session, user_a, user_b)
    return bool(f and f.status == FriendshipStatus.ACCEPTED.value)


async def send_room_invite(
    session: AsyncSession,
    *,
    from_user_id: str,
    to_user_id: str,
    game_id: str,
    join_code: str,
    room_name: str | None,
    scenario_name: str,
) -> RoomInvite:
    if not await _are_friends(session, from_user_id, to_user_id):
        raise FriendServiceError("you can only invite friends")
    invite = RoomInvite(
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        game_id=game_id,
        join_code=join_code,
        room_name=room_name,
        scenario_name=scenario_name,
    )
    session.add(invite)
    await session.commit()
    return invite


async def list_received_invites(session: AsyncSession, *, user_id: str) -> list[InviteEntry]:
    rows = (
        await session.execute(
            select(RoomInvite, User.username)
            .join(User, User.id == RoomInvite.from_user_id)
            .join(Game, Game.id == RoomInvite.game_id)
            .where(RoomInvite.to_user_id == user_id, Game.status == "lobby")
            .order_by(RoomInvite.created_at.desc())
        )
    ).all()
    return [
        InviteEntry(
            id=invite.id,
            from_username=username,
            game_id=invite.game_id,
            join_code=invite.join_code,
            room_name=invite.room_name,
            scenario_name=invite.scenario_name,
        )
        for invite, username in rows
    ]


async def dismiss_invite(session: AsyncSession, *, user_id: str, invite_id: str) -> None:
    invite = (
        await session.execute(select(RoomInvite).where(RoomInvite.id == invite_id))
    ).scalar_one_or_none()
    if not invite:
        return
    if invite.to_user_id != user_id:
        raise FriendServiceError("not the recipient of this invite")
    await session.delete(invite)
    await session.commit()

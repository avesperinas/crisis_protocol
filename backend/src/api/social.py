"""Friends, room invites, and profile stats/history endpoints."""

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user, get_session
from src.models import User
from src.schemas.social import (
    FriendEntryView,
    FriendRequestCreate,
    FriendsListView,
    GameHistoryEntryView,
    InviteEntryView,
    RoomInviteCreate,
    UserSearchResult,
    UserStatsView,
)
from src.services.friend_service import (
    FriendServiceError,
    accept_friend_request,
    dismiss_invite,
    list_friendships,
    list_received_invites,
    remove_friendship,
    search_users,
    send_friend_request,
    send_room_invite,
)
from src.services.stats_service import compute_user_stats, list_user_games

router = APIRouter(tags=["social"])


@router.get("/api/users/search", response_model=list[UserSearchResult])
async def search_users_endpoint(
    q: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[UserSearchResult]:
    results = await search_users(session, query=q, exclude_user_id=user.id)
    return [UserSearchResult(id=u.id, username=u.username) for u in results]


@router.get("/api/users/me/stats", response_model=UserStatsView)
async def my_stats(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> UserStatsView:
    stats = await compute_user_stats(session, user_id=user.id)
    return UserStatsView(**asdict(stats))


@router.get("/api/users/me/games", response_model=list[GameHistoryEntryView])
async def my_games(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> list[GameHistoryEntryView]:
    games = await list_user_games(session, user_id=user.id)
    return [GameHistoryEntryView(**asdict(g)) for g in games]


@router.get("/api/friends", response_model=FriendsListView)
async def get_friends(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> FriendsListView:
    entries = await list_friendships(session, user_id=user.id)
    invites = await list_received_invites(session, user_id=user.id)
    return FriendsListView(
        friends=[FriendEntryView(**asdict(e)) for e in entries],
        invites=[InviteEntryView(**asdict(i)) for i in invites],
    )


@router.post("/api/friends/request")
async def request_friend(
    payload: FriendRequestCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    try:
        await send_friend_request(session, requester_id=user.id, recipient_username=payload.username)
    except FriendServiceError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}


@router.post("/api/friends/{friendship_id}/accept")
async def accept_friend(
    friendship_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    try:
        await accept_friend_request(session, user_id=user.id, friendship_id=friendship_id)
    except FriendServiceError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}


@router.delete("/api/friends/{friendship_id}")
async def remove_friend(
    friendship_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    try:
        await remove_friendship(session, user_id=user.id, friendship_id=friendship_id)
    except FriendServiceError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}


@router.post("/api/friends/invite")
async def invite_friend(
    payload: RoomInviteCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    try:
        await send_room_invite(
            session,
            from_user_id=user.id,
            to_user_id=payload.to_user_id,
            game_id=payload.game_id,
            join_code=payload.join_code,
            room_name=payload.room_name,
            scenario_name=payload.scenario_name,
        )
    except FriendServiceError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}


@router.delete("/api/friends/invites/{invite_id}")
async def dismiss_invite_endpoint(
    invite_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
) -> dict:
    try:
        await dismiss_invite(session, user_id=user.id, invite_id=invite_id)
    except FriendServiceError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}

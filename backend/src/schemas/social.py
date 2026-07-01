"""Pydantic DTOs for friends, room invites, and profile stats/history."""

from pydantic import BaseModel, ConfigDict


class UserSearchResult(BaseModel):
    id: str
    username: str


class FriendRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str


class FriendEntryView(BaseModel):
    friendship_id: str
    user_id: str
    username: str
    status: str
    direction: str  # incoming | outgoing | mutual


class RoomInviteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to_user_id: str
    game_id: str
    join_code: str
    room_name: str | None = None
    scenario_name: str


class InviteEntryView(BaseModel):
    id: str
    from_username: str
    game_id: str
    join_code: str
    room_name: str | None
    scenario_name: str


class FriendsListView(BaseModel):
    friends: list[FriendEntryView]
    invites: list[InviteEntryView]


class GameHistoryEntryView(BaseModel):
    game_id: str
    scenario_id: str
    scenario_name: str
    role_id: str
    role_name: str
    finished_at: str | None
    score_total: int
    rank: int
    player_count: int
    public_objective_met: bool
    hidden_objective_met: bool


class UserStatsView(BaseModel):
    games_played: int
    wins: int
    favorite_scenario: str | None
    favorite_faction: str | None
    avg_decision_quality: float
    avg_coherence: float
    public_objective_rate: float
    hidden_objective_rate: float

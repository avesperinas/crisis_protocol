import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from src.models.pact import Pact
    from src.models.player import Player
    from src.models.turn import Turn


class GameStatus(str, enum.Enum):
    LOBBY = "lobby"
    BRIEFING = "briefing"
    ACTIVE = "active"
    RESOLVING = "resolving"
    FINISHED = "finished"


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    scenario_id: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default=GameStatus.LOBBY.value)
    current_turn: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_turns: Mapped[int] = mapped_column(Integer, nullable=False)
    tension: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    crisis_card: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Fase 7 — multiplayer
    mode: Mapped[str] = mapped_column(String, nullable=False, default="solo")
    join_code: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    host_role_id: Mapped[str | None] = mapped_column(String, nullable=True)
    room_name: Mapped[str | None] = mapped_column(String, nullable=True)
    # Fase C — per-game turn pacing. NULL = fall back to settings.turn_timeout_seconds.
    turn_timeout_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    players: Mapped[list["Player"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )
    turns: Mapped[list["Turn"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )
    pacts: Mapped[list["Pact"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from src.models.action import Action
    from src.models.game import Game
    from src.models.message import Message


class TurnStatus(str, enum.Enum):
    COLLECTING = "collecting"
    RESOLVING = "resolving"
    FINISHED = "finished"


class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id: Mapped[str] = mapped_column(
        String, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String, default=TurnStatus.COLLECTING.value, nullable=False)
    tension_at_start: Mapped[int] = mapped_column(Integer, nullable=False)
    tension_at_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)

    game: Mapped["Game"] = relationship(back_populates="turns")
    actions: Mapped[list["Action"]] = relationship(
        back_populates="turn", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="turn", cascade="all, delete-orphan"
    )

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from src.models.action import Action
    from src.models.game import Game


class Player(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id: Mapped[str] = mapped_column(
        String, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[str] = mapped_column(String, nullable=False)
    is_ai: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True)
    resources: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    briefing: Mapped[str | None] = mapped_column(Text, nullable=True)
    public_objective_status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    hidden_objective_status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    # Public trustworthiness (0–100, starts neutral at 50). Moves when the
    # evaluation detects kept/broken promises and when the player breaks pacts.
    credibility: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    game: Mapped["Game"] = relationship(back_populates="players")
    actions: Mapped[list["Action"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
        foreign_keys="Action.player_id",
    )

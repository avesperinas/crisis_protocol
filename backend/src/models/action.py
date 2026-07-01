import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from src.models.player import Player
    from src.models.turn import Turn


class Posture(str, enum.Enum):
    CONFRONTATIONAL = "confrontational"
    COOPERATIVE = "cooperative"
    AMBIGUOUS = "ambiguous"


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    turn_id: Mapped[str] = mapped_column(
        String, ForeignKey("turns.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[str] = mapped_column(
        String, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    posture: Mapped[str] = mapped_column(String, nullable=False)
    tokens_mil: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_dip: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_eco: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_int: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    directive: Mapped[str] = mapped_column(Text, nullable=False)
    coherence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    posture_modifier: Mapped[float | None] = mapped_column(Float, nullable=True)
    decision_quality: Mapped[float | None] = mapped_column(Float, nullable=True)
    effective_multiplier: Mapped[float | None] = mapped_column(Float, nullable=True)
    effects: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    intel_report: Mapped[str | None] = mapped_column(Text, nullable=True)

    turn: Mapped["Turn"] = relationship(back_populates="actions")
    player: Mapped["Player"] = relationship(back_populates="actions", foreign_keys=[player_id])

import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from src.models.turn import Turn


class ProposalStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    turn_id: Mapped[str] = mapped_column(
        String, ForeignKey("turns.id", ondelete="CASCADE"), nullable=False
    )
    from_player_id: Mapped[str] = mapped_column(String, ForeignKey("players.id"), nullable=False)
    to_player_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("players.id"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_proposal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    proposal_type: Mapped[str | None] = mapped_column(String, nullable=True)
    proposal_status: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    turn: Mapped["Turn"] = relationship(back_populates="messages")

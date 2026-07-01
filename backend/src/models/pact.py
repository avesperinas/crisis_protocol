import enum
import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base

if TYPE_CHECKING:
    from src.models.game import Game


class PactType(str, enum.Enum):
    ALLIANCE = "alliance"
    NON_AGGRESSION = "non_aggression"
    TRADE = "trade"
    INTEL_SHARE = "intel_share"
    MEDIATION = "mediation"


class Pact(Base):
    __tablename__ = "pacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    game_id: Mapped[str] = mapped_column(
        String, ForeignKey("games.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String, nullable=False)
    player_a_id: Mapped[str] = mapped_column(String, ForeignKey("players.id"), nullable=False)
    player_b_id: Mapped[str] = mapped_column(String, ForeignKey("players.id"), nullable=False)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_turn: Mapped[int] = mapped_column(Integer, nullable=False)
    broken_turn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    broken_by_player_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("players.id"), nullable=True
    )
    terms: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    game: Mapped["Game"] = relationship(back_populates="pacts")

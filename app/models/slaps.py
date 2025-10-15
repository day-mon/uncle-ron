from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class SlapEntry(Base):
    __tablename__ = "slap_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    slapper_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )  # User who did the slapping
    slapped_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )  # User who got slapped
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "slapper_id": self.slapper_id,
            "slapped_id": self.slapped_id,
            "created_at": self.created_at,
        }

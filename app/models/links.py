from datetime import datetime
from typing import Dict, Any

from sqlalchemy import BigInteger, String, Text, DateTime, Column, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class LinkEntry(Base):
    __tablename__ = "link_entries"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, nullable=False)
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "user_id": self.user_id,
            "hostname": self.hostname,
            "url": self.url,
            "created_at": self.created_at,
        }
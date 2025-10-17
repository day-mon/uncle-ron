from datetime import datetime
from typing import Any

from pydantic import BaseModel, field_validator, Field, ConfigDict
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    String,
    Text,
    Column,
    ForeignKey,
    Float,
    Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import json


class Base(DeclarativeBase):
    pass


class GuildSettings(Base):
    __tablename__ = "guild_settings"

    guild_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    fact_check_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    grok_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    qotd_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    settings_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    # Relationship with ThreadSettings
    threads = relationship("ThreadSettings", back_populates="guild")

    def get_settings_dict(self) -> dict[str, Any]:
        """Get the JSON settings as a dictionary."""
        try:
            return json.loads(self.settings_json) if self.settings_json else {}
        except json.JSONDecodeError:
            return {}

    def set_settings_dict(self, settings: dict[str, Any]) -> None:
        """Set the JSON settings from a dictionary."""
        self.settings_json = json.dumps(settings)

    def to_dict(self) -> dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "guild_id": self.guild_id,
            "ai_enabled": self.ai_enabled,
            "fact_check_enabled": self.fact_check_enabled,
            "grok_enabled": self.grok_enabled,
            "qotd_enabled": self.qotd_enabled,
            "settings_json": self.get_settings_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class GuildSettingsSchema(BaseModel):
    """Pydantic schema for guild settings."""

    model_config = ConfigDict(from_attributes=True)

    guild_id: int
    ai_enabled: bool = False
    fact_check_enabled: bool = False
    grok_enabled: bool = False
    qotd_enabled: bool = False
    settings_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("guild_id")
    @classmethod
    def validate_guild_id(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("guild_id must be positive")
        return v

    @field_validator("settings_json", mode="before")
    @classmethod
    def validate_settings_json(cls, v: Any) -> dict[str, Any]:
        """Convert string JSON to dictionary if needed."""
        if isinstance(v, str):
            try:
                return json.loads(v) if v else {}
            except json.JSONDecodeError:
                return {}
        elif isinstance(v, dict):
            return v
        else:
            return {}


class GuildSettingUpdate(BaseModel):
    """Schema for updating a single guild setting."""

    setting: str
    value: Any

    @field_validator("setting")
    @classmethod
    def validate_setting(cls, v: str) -> str:
        allowed = ["ai_enabled", "fact_check_enabled", "grok_enabled", "qotd_enabled"]
        if v not in allowed:
            raise ValueError(f"Invalid setting: {v}. Must be one of {allowed}")
        return v


class ThreadSettings(Base):
    __tablename__ = "thread_settings"

    thread_id = Column(BigInteger, primary_key=True)
    guild_id = Column(BigInteger, ForeignKey("guild_settings.guild_id"), nullable=False)
    model = Column(String, nullable=False)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)

    guild = relationship("GuildSettings", back_populates="threads")

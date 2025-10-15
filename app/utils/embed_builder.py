"""
Embed builder utility for creating Discord embeds with common patterns.
"""

from datetime import datetime, timezone
from typing import Any
from discord import Embed


class EmbedBuilder:
    """Builder class for creating Discord embeds with common patterns."""

    def __init__(self):
        self._embed = Embed()

    @staticmethod
    def create(
        title: str | None = None,
        description: str | None = None,
        color=None,
        timestamp: datetime | None = None,
    ) -> Embed:
        """Create and return an Embed directly with common parameters.

        Args:
            title: The embed title
            description: The embed description
            color: The embed color
            timestamp: The embed timestamp (defaults to current time if None)

        Returns:
            A configured Discord Embed object
        """
        embed = Embed(title=title, description=description, color=color)
        if timestamp:
            embed.timestamp = timestamp
        elif timestamp is None:
            embed.timestamp = datetime.now(timezone.utc)
        return embed

    def title(self, title: str) -> "EmbedBuilder":
        """Set the embed title."""
        self._embed.title = title
        return self

    def description(self, description: str) -> "EmbedBuilder":
        """Set the embed description."""
        self._embed.description = description
        return self

    def color(self, color: int) -> "EmbedBuilder":
        """Set the embed color."""
        self._embed.color = color
        return self

    def timestamp(self, timestamp: datetime | None = None) -> "EmbedBuilder":
        """Set the embed timestamp."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        self._embed.timestamp = timestamp
        return self

    def add_field(self, name: str, value: str, inline: bool = False) -> "EmbedBuilder":
        """Add a field to the embed."""
        self._embed.add_field(name=name, value=value, inline=inline)
        return self

    def add_fields(self, fields: list[dict[str, Any]]) -> "EmbedBuilder":
        """Add multiple fields to the embed."""
        for field in fields:
            self._embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", False),
            )
        return self

    def footer(self, text: str, icon_url: str | None = None) -> "EmbedBuilder":
        """Set the embed footer."""
        self._embed.set_footer(text=text, icon_url=icon_url)
        return self

    def thumbnail(self, url: str) -> "EmbedBuilder":
        """Set the embed thumbnail."""
        self._embed.set_thumbnail(url=url)
        return self

    def image(self, url: str) -> "EmbedBuilder":
        """Set the embed image."""
        self._embed.set_image(url=url)
        return self

    def author(
        self, name: str, url: str | None = None, icon_url: str | None = None
    ) -> "EmbedBuilder":
        """Set the embed author."""
        self._embed.set_author(name=name, url=url, icon_url=icon_url)
        return self

    def build(self) -> Embed:
        """Build and return the embed."""
        return self._embed

    @classmethod
    def error_embed(cls, title: str, description: str) -> "EmbedBuilder":
        """Create an error embed."""
        return (
            cls()
            .title(f"❌ {title}")
            .description(description)
            .color(0xFF0000)
            .timestamp()
        )

    @classmethod
    def success_embed(cls, title: str, description: str) -> "EmbedBuilder":
        """Create a success embed."""
        return (
            cls()
            .title(f"✅ {title}")
            .description(description)
            .color(0x00FF00)
            .timestamp()
        )

    @classmethod
    def info_embed(cls, title: str, description: str) -> "EmbedBuilder":
        """Create an info embed."""
        return (
            cls()
            .title(f"ℹ️ {title}")
            .description(description)
            .color(0x0099FF)
            .timestamp()
        )

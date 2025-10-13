from typing import overload

import discord
from discord import Interaction, InteractionResponse

from app.utils.logger import get_logger

logger = get_logger(__name__)


@overload
async def send(
    interaction: Interaction,
    *,
    content: str,
    ephemeral: bool = False,
    embed: discord.Embed = None,
): ...


@overload
async def send(
    interaction: Interaction,
    *,
    embed: discord.Embed,
    content: str | None = None,
    ephemeral: bool = False,
): ...


async def send(
    interaction: Interaction,
    *,
    content: str | None = None,
    ephemeral: bool = True,
    embed: discord.Embed = None,
):
    """
    Sends a message to the interaction, using response or followup as appropriate.
    """

    response = interaction.response
    try:
        if response.is_done():
            await interaction.followup.send(content, ephemeral=ephemeral, embed=embed)
        else:
            await response.send_message(content, ephemeral=ephemeral, embed=embed)
    except Exception:
        try:
            await interaction.followup.send(content, ephemeral=ephemeral, embed=embed)
        except Exception:
            logger.exception("Failed to send followup message")
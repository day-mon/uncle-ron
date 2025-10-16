"""
Utility module for centralized Discord command checks.
"""

import discord
from discord.ext import commands
from typing import Callable, Awaitable, Coroutine, Any

from app.database import db
from app.utils.logger import get_logger

logger = get_logger(__name__)

type CheckFunction[T] = Callable[[T], Awaitable[bool]]


async def guild_only_check(ctx: commands.Context | discord.Interaction) -> bool:
    """
    Check if the command is being used in a guild.

    This function can be used with both @commands.check() and @app_commands.check()
    """
    if isinstance(ctx, discord.Interaction):
        if ctx.guild_id is None:
            await ctx.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return False
        return True
    else:
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.")
            return False
        return True


async def feature_enabled_check(
    ctx: commands.Context | discord.Interaction, feature: str
) -> bool:
    """
    Check if a specific feature is enabled for the guild.

    Args:
        ctx: The command context or interaction
        feature: The feature name to check

    This function can be used with both @commands.check() and @app_commands.check()
    by creating a lambda or partial function that passes the feature parameter.
    """
    guild_id = None

    if isinstance(ctx, discord.Interaction):
        guild_id = ctx.guild_id
        if guild_id is None:
            await ctx.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return False
    else:
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.")
            return False
        guild_id = ctx.guild.id

    is_enabled = await db.is_feature_enabled(guild_id, feature)

    if not is_enabled:
        message = f"The '{feature}' feature is not enabled for this server."
        if isinstance(ctx, discord.Interaction):
            if not ctx.response.is_done():
                await ctx.response.send_message(message, ephemeral=True)
            else:
                await ctx.followup.send(message, ephemeral=True)
        else:
            await ctx.send(message)

        logger.info(
            f"Feature check failed: '{feature}' is not enabled for guild {guild_id}"
        )
        return False

    return True


async def is_admin_check(ctx: commands.Context | discord.Interaction) -> bool:
    """
    Check if the user has administrator permissions.

    This function can be used with both @commands.check() and @app_commands.check()
    """
    user = None
    guild = None

    if isinstance(ctx, discord.Interaction):
        user = ctx.user
        guild = ctx.guild
        if guild is None:
            await ctx.response.send_message(
                "This command can only be used in a server.", ephemeral=True
            )
            return False
    else:
        user = ctx.author
        guild = ctx.guild
        if guild is None:
            await ctx.send("This command can only be used in a server.")
            return False

    member = guild.get_member(user.id)
    if member is None:
        return False

    if member.guild_permissions.administrator:
        return True

    message = "You need administrator permissions to use this command."
    if isinstance(ctx, discord.Interaction):
        if not ctx.response.is_done():
            await ctx.response.send_message(message, ephemeral=True)
        else:
            await ctx.followup.send(message, ephemeral=True)
    else:
        await ctx.send(message)

    return False


def create_feature_check(
    feature: str,
) -> Callable[[commands.Context | discord.Interaction], Coroutine[Any, Any, bool]]:
    """
    Create a feature check function for a specific feature.

    This is a helper function to create a check function that can be used with
    @commands.check() or @app_commands.check()

    Args:
        feature: The feature name to check
    """

    async def check_func(ctx: commands.Context | discord.Interaction) -> bool:
        return await feature_enabled_check(ctx, feature)

    return check_func

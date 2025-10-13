import discord
from discord import Interaction, app_commands
from discord.ext.commands import (
    Cog,
    Bot,
    hybrid_command,
    Context,
    has_guild_permissions,
)
from discord.app_commands import Range

from app.database import db
from app.utils import EmbedBuilder
from app.utils.check_utils import guild_only_check, is_admin_check
from app.utils.logger import get_logger
from propcache import cached_property


class Settings(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        
    @cached_property
    def logger(self):
        """Get a logger for this cog."""
        return get_logger(self.__class__.__name__)

    # Using centralized checks from app.utils.check_utils

    @hybrid_command(
        name="settings",
        description="View current guild settings",
    )
    @app_commands.check(guild_only_check)
    async def view_settings(self, ctx: Context):
        """View the current guild settings."""

        settings = await db.get_guild_settings(ctx.guild.id)

        embed = discord.Embed(
            title="🔧 Guild Settings",
            description=f"Settings for **{ctx.guild.name}**",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )

        ai_status = "✅ Enabled" if settings.ai_enabled else "❌ Disabled"
        fact_check_status = (
            "✅ Enabled" if settings.fact_check_enabled else "❌ Disabled"
        )
        grok_status = "✅ Enabled" if settings.grok_enabled else "❌ Disabled"
        qotd_status = "✅ Enabled" if settings.qotd_enabled else "❌ Disabled"

        embed.add_field(
            name="🤖 AI Features",
            value=f"**Ask Command:** {ai_status}\n**Fact Check:** {fact_check_status}\n**Grok AI:** {grok_status}\n**QOTD:** {qotd_status}",
            inline=False,
        )

        if settings := await db.get_guild_settings_json(ctx.guild.id):
            embed.add_field(
                name="⚙️ Additional Settings",
                value=f"```json\n{str(settings.settings_json)[:500]}{'...' if len(str(settings.settings_json)) > 500 else ''}\n```",
                inline=False,
            )

        embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
        await ctx.send(embed=embed)

    @hybrid_command(
        name="enable",
        description="Enable a feature for this guild",
    )
    @app_commands.check(guild_only_check)
    @app_commands.check(is_admin_check)
    @app_commands.describe(
        feature="The feature to enable, Choose from: ai, factcheck, grok, qotd",
    )
    async def enable_feature(self, ctx: Context, *, feature: str):
        """Enable a specific feature for the guild."""

        feature_map = {
            "ai": "ai_enabled",
            "factcheck": "fact_check_enabled",
            "grok": "grok_enabled",
            "qotd": "qotd_enabled",
        }

        if feature.lower() not in feature_map:
            await ctx.send(
                "❌ Invalid feature. Available options: `ai`, `factcheck`, `grok`, `qotd`",
                ephemeral=True,
            )
            return

        setting_name = feature_map[feature.lower()]

        try:
            await db.update_guild_setting(ctx.guild.id, setting_name, True)
        except ValueError as e:
            await ctx.send(f"❌ Error: {str(e)}", ephemeral=True)
            return

        feature_names = {
            "ai": "AI Ask Command",
            "factcheck": "Fact Check",
            "grok": "Grok AI",
            "qotd": "Question of the Day",
        }

        embed = EmbedBuilder.success_embed(
            title=f"{feature_names[feature.lower()]} Enabled",
            description=f"**{feature_names[feature.lower()]}** has been enabled for this guild!",
        ).build()

        await ctx.send(embed=embed, ephemeral=True)

    @hybrid_command(
        name="disable",
        description="Disable a feature for this guild",
    )
    @app_commands.check(guild_only_check)
    @app_commands.check(is_admin_check)
    @app_commands.describe(feature="The feature to disable (ai, factcheck, grok, qotd)")
    async def disable_feature(self, ctx: Context, *, feature: str):
        """Disable a specific feature for the guild."""

        feature_map = {
            "ai": "ai_enabled",
            "factcheck": "fact_check_enabled",
            "grok": "grok_enabled",
            "qotd": "qotd_enabled",
        }

        if feature.lower() not in feature_map:
            await ctx.send(
                "❌ Invalid feature. Available options: `ai`, `factcheck`, `grok`, `qotd`",
                ephemeral=True,
            )
            return

        setting_name = feature_map[feature.lower()]

        try:
            await db.update_guild_setting(ctx.guild.id, setting_name, False)
        except ValueError as e:
            await ctx.send(f"❌ Error: {str(e)}", ephemeral=True)
            return

        feature_names = {
            "ai": "AI Ask Command",
            "factcheck": "Fact Check",
            "grok": "Grok AI",
            "qotd": "Question of the Day",
        }

        embed = EmbedBuilder.error_embed(
            title=f"{feature_names[feature.lower()]} Disabled",
            description=f"**{feature_names[feature.lower()]}** has been disabled for this guild!",
        ).build()

        await ctx.send(embed=embed, ephemeral=True)

    @hybrid_command(
        name="setconfig",
        description="Set a custom configuration value",
    )
    @app_commands.check(guild_only_check)
    @app_commands.check(is_admin_check)
    @app_commands.describe(key="The configuration key", value="The configuration value")
    async def set_config(self, ctx: Context, *, key: str, value: str):
        """Set a custom configuration value for the guild."""

        current_settings = await db.get_guild_settings_json(ctx.guild.id)

        current_settings[key] = value
        await db.update_guild_settings_json(ctx.guild.id, current_settings)

        embed = EmbedBuilder.success_embed(
            title="Configuration Updated",
            description=f"Configuration `{key}` set to `{value}` for this guild!",
        ).build()

        await ctx.send(embed=embed, ephemeral=True)

    @hybrid_command(
        name="getconfig",
        description="Get a custom configuration value",
    )
    @app_commands.check(guild_only_check)
    @app_commands.describe(key="The configuration key to retrieve")
    async def get_config(self, ctx: Context, *, key: str):
        """Get a custom configuration value for the guild."""

        current_settings = await db.get_guild_settings_json(ctx.guild.id)

        if key not in current_settings:
            embed = EmbedBuilder.error_embed(
                title="Configuration Not Found",
                description=f"Configuration key `{key}` not found.",
            ).build()
            await ctx.send(embed=embed, ephemeral=True)
            return

        embed = EmbedBuilder.info_embed(
            title="Configuration Value",
            description=f"**{key}:** `{current_settings[key]}`",
        ).build()

        await ctx.send(embed=embed)

    @hybrid_command(
        name="delconfig",
        description="Delete a custom configuration value",
    )
    @app_commands.check(guild_only_check)
    @app_commands.check(is_admin_check)
    @app_commands.describe(key="The configuration key to delete")
    async def del_config(self, ctx: Context, *, key: str):
        """Delete a custom configuration value for the guild."""

        current_settings = await db.get_guild_settings_json(ctx.guild.id)

        if key not in current_settings:
            embed = EmbedBuilder.error_embed(
                title="Configuration Not Found",
                description=f"Configuration key `{key}` not found.",
            ).build()
            await ctx.send(embed=embed, ephemeral=True)
            return

        del current_settings[key]
        await db.update_guild_settings_json(ctx.guild.id, current_settings)

        embed = EmbedBuilder.success_embed(
            title="Configuration Deleted",
            description=f"Configuration key `{key}` deleted!",
        ).build()

        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(Settings(bot))

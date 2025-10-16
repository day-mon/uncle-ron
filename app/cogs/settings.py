import discord
from discord import app_commands
from discord.ext.commands import (
    Cog,
    Bot,
    hybrid_group,
    Context,
)

from app.database import db
from app.models.settings import FeatureSettings
from app.utils import EmbedBuilder
from app.utils.check_utils import guild_only_check, is_admin_check
from app.utils.logger import get_logger
from propcache import cached_property

# Module-level instance for use in decorators
_feature_settings = FeatureSettings()


class Settings(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.feature_settings = FeatureSettings()

    @cached_property
    def logger(self):
        """Get a logger for this cog."""
        return get_logger(self.__class__.__name__)

    @hybrid_group(
        name="settings",
        description="Manage guild settings and configuration",
        fallback="view"
    )
    @app_commands.check(guild_only_check)
    async def settings_group(self, ctx: Context):
        """View the current guild settings."""
        settings = await db.get_guild_settings(ctx.guild.id)

        embed = discord.Embed(
            title="🔧 Guild Settings",
            description=f"Settings for **{ctx.guild.name}**",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )

        # Build feature status using dictionary mapping
        feature_values = {
            "ai_enabled": settings.ai_enabled,
            "fact_check_enabled": settings.fact_check_enabled,
            "grok_enabled": settings.grok_enabled,
            "qotd_enabled": settings.qotd_enabled,
        }
        
        feature_statuses = []
        for feature in self.feature_settings.features:
            current_status = feature_values.get(feature.value, False)
            status_text = "✅ Enabled" if current_status else "❌ Disabled"
            feature_statuses.append(f"**{feature.description}:** {status_text}")

        embed.add_field(
            name="🤖 AI Features",
            value="\n".join(feature_statuses),
            inline=False,
        )

        json_settings = await db.get_guild_settings_json(ctx.guild.id)
        if json_settings and json_settings.settings_json:
            embed.add_field(
                name="⚙️ Additional Settings",
                value=f"```json\n{str(json_settings.settings_json)[:500]}{'...' if len(str(json_settings.settings_json)) > 500 else ''}\n```",
                inline=False,
            )

        embed.set_footer(text=f"Guild ID: {ctx.guild.id}")
        await ctx.send(embed=embed)

    @settings_group.error
    async def settings_group_error(self, ctx: Context, error):
        """Handle errors for settings group"""
        self.logger.error(f"Error in settings group for guild {ctx.guild.id}: {error}")
        embed = EmbedBuilder.error_embed(
            title="Error",
            description="An error occurred while retrieving the guild settings.",
        ).build()
        await ctx.send(embed=embed)

    @settings_group.command(
        name="enable",
        description="Enable a feature for this guild",
    )
    @app_commands.check(is_admin_check)
    @app_commands.describe(
        feature=f"The feature to enable. Choose from: {', '.join(_feature_settings.feature_map.keys())}",
    )
    async def enable_feature(self, ctx: Context, *, feature: str):
        """Enable a specific feature for the guild."""
        if (feature_key := feature.lower()) not in self.feature_settings.feature_map:
            available_features = ", ".join(f"`{f}`" for f in self.feature_settings.feature_map.keys())
            await ctx.send(
                f"❌ Invalid feature. Available options: {available_features}",
                ephemeral=True,
            )
            return

        setting_name = self.feature_settings.feature_map[feature_key]

        try:
            await db.update_guild_setting(ctx.guild.id, setting_name, True)
        except ValueError as e:
            await ctx.send(f"❌ Error: {str(e)}", ephemeral=True)
            return

        feature_name = self.feature_settings.feature_names[feature_key]
        embed = EmbedBuilder.success_embed(
            title=f"{feature_name} Enabled",
            description=f"**{feature_name}** has been enabled for this guild!",
        ).build()

        await ctx.send(embed=embed, ephemeral=True)

    @settings_group.command(
        name="disable",
        description="Disable a feature for this guild",
    )
    @app_commands.check(is_admin_check)
    @app_commands.describe(
        feature=f"The feature to disable. Choose from: {', '.join(_feature_settings.feature_map.keys())}"
    )
    async def disable_feature(self, ctx: Context, *, feature: str):
        """Disable a specific feature for the guild."""
        if (feature_key := feature.lower()) not in self.feature_settings.feature_map:
            available_features = ", ".join(f"`{f}`" for f in self.feature_settings.feature_map.keys())
            await ctx.send(
                f"❌ Invalid feature. Available options: {available_features}",
                ephemeral=True,
            )
            return

        setting_name = self.feature_settings.feature_map[feature_key]

        try:
            await db.update_guild_setting(ctx.guild.id, setting_name, False)
        except ValueError as e:
            await ctx.send(f"❌ Error: {str(e)}", ephemeral=True)
            return

        feature_name = self.feature_settings.feature_names[feature_key]
        embed = EmbedBuilder.error_embed(
            title=f"{feature_name} Disabled",
            description=f"**{feature_name}** has been disabled for this guild!",
        ).build()

        await ctx.send(embed=embed, ephemeral=True)

    @hybrid_group(
        name="config",
        description="Manage custom configuration values",
        fallback="get"
    )
    @app_commands.check(guild_only_check)
    @app_commands.describe(key="The configuration key to retrieve")
    async def config_group(self, ctx: Context, *, key: str):
        """Get a custom configuration value for the guild."""
        if not (current_settings := await db.get_guild_settings_json(ctx.guild.id)):
            embed = EmbedBuilder.error_embed(
                title="Configuration Not Found",
                description="No configuration settings found for this guild.",
            ).build()
            await ctx.send(embed=embed)
            return

        if not (settings_dict := current_settings.to_dict()) or key not in settings_dict:
            embed = EmbedBuilder.error_embed(
                title="Configuration Not Found",
                description=f"The key `{key}` does not exist in the configuration.",
            ).build()
            await ctx.send(embed=embed)
            return

        embed = EmbedBuilder.info_embed(
            title="Configuration Value",
            description=f"**{key}:** `{settings_dict[key]}`",
        ).build()
        await ctx.send(embed=embed)

    @config_group.error
    async def config_group_error(self, ctx: Context, error):
        """Handle errors for config group"""
        self.logger.error(f"Error in config group for guild {ctx.guild.id}: {error}")
        embed = EmbedBuilder.error_embed(
            title="Error",
            description="An error occurred while retrieving the configuration.",
        ).build()
        await ctx.send(embed=embed)

    @config_group.command(
        name="set",
        description="Set a custom configuration value",
    )
    @app_commands.check(is_admin_check)
    @app_commands.describe(key="The configuration key", value="The configuration value")
    async def set_config(self, ctx: Context, key: str, value: str):
        """Set a custom configuration value for the guild."""
        if not (current_settings := await db.get_guild_settings_json(ctx.guild.id)):
            embed = EmbedBuilder.error_embed(
                title="Configuration Error",
                description="No configuration settings found for this guild.",
            ).build()
            await ctx.send(embed=embed, ephemeral=True)
            return

        settings_dict = current_settings.to_dict()
        settings_dict[key] = value
        await db.update_guild_settings_json(ctx.guild.id, settings_dict)

        embed = EmbedBuilder.success_embed(
            title="Configuration Updated",
            description=f"Configuration `{key}` set to `{value}` for this guild!",
        ).build()

        await ctx.send(embed=embed, ephemeral=True)

    @set_config.error
    async def set_config_error(self, ctx: Context, error):
        """Handle errors for set_config command"""
        self.logger.error(f"Error in set_config for guild {ctx.guild.id}: {error}")
        embed = EmbedBuilder.error_embed(
            title="Error",
            description="An error occurred while updating the configuration.",
        ).build()
        await ctx.send(embed=embed, ephemeral=True)

    @config_group.command(
        name="delete",
        description="Delete a custom configuration value",
    )
    @app_commands.check(is_admin_check)
    @app_commands.describe(key="The configuration key to delete")
    async def delete_config(self, ctx: Context, *, key: str):
        """Delete a custom configuration value for the guild."""
        if not (current_settings := await db.get_guild_settings_json(ctx.guild.id)):
            embed = EmbedBuilder.error_embed(
                title="Configuration Not Found",
                description="No configuration settings found for this guild.",
            ).build()
            await ctx.send(embed=embed, ephemeral=True)
            return

        if not (settings_dict := current_settings.to_dict()) or key not in settings_dict:
            embed = EmbedBuilder.error_embed(
                title="Configuration Not Found",
                description=f"The key `{key}` does not exist in the configuration.",
            ).build()
            await ctx.send(embed=embed, ephemeral=True)
            return

        # Remove the key from settings
        del settings_dict[key]
        await db.update_guild_settings_json(ctx.guild.id, settings_dict)

        embed = EmbedBuilder.success_embed(
            title="Configuration Deleted",
            description=f"Configuration key `{key}` deleted!",
        ).build()

        await ctx.send(embed=embed, ephemeral=True)

    @delete_config.error
    async def delete_config_error(self, ctx: Context, error):
        """Handle errors for delete_config command"""
        self.logger.error(f"Error in delete_config for guild {ctx.guild.id}: {error}")
        embed = EmbedBuilder.error_embed(
            title="Error",
            description="An error occurred while deleting the configuration.",
        ).build()
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(Settings(bot))

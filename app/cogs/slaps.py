import random

import discord
from discord import app_commands
from discord.ext.commands import Cog, Bot, hybrid_group, Context
from propcache import cached_property

from app.utils.embed_builder import EmbedBuilder
from app.database import db
from app.utils.check_utils import guild_only_check
from app.utils.logger import get_logger


class Slaps(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @cached_property
    def logger(self):
        """Get a logger for this cog."""
        return get_logger(self.__class__.__name__)

    @property
    def slap_messages(self):
        """Various slap messages for fun variety."""
        return [
            "{slapper} slaps {slapped} around a bit with a large trout! 🐟",
            "{slapper} gives {slapped} a mighty slap! 👋",
            "{slapper} slaps {slapped} with a wet noodle! 🍜",
            "{slapper} delivers a crisp slap to {slapped}! ✋",
            "{slapper} slaps {slapped} with a rubber chicken! 🐔",
            "{slapper} gives {slapped} a gentle slap on the wrist! 👋",
            "{slapper} slaps {slapped} with a pillow! 🛏️",
            "{slapper} delivers an epic slap to {slapped}! 💥",
            "{slapper} slaps {slapped} with a banana! 🍌",
            "{slapper} gives {slapped} a theatrical slap! 🎭",
        ]

    @hybrid_group(name="slap", description="Slap commands")
    async def slap(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = (
                EmbedBuilder()
                .title("👋 Slap Commands")
                .description("Slap someone or view the slap leaderboard!")
                .color(discord.Color.red())
                .add_field(
                    name="Available Commands",
                    value=(
                        "`/slap user @someone` - Slap a user\n"
                        "`/slap leaderboard` - View who's been slapped the most\n"
                        "`/slap stats` - View your personal slap statistics"
                    ),
                    inline=False,
                )
                .build()
            )
            await ctx.send(embed=embed)

    @slap.command(name="user", description="Slap someone!")
    @app_commands.describe(target="The user you want to slap")
    @app_commands.check(guild_only_check)
    async def slap_user(self, ctx: Context, target: discord.Member):
        # Prevent self-slapping
        if target.id == ctx.author.id:
            embed = (
                EmbedBuilder()
                .title("🤔 Self-Slap Denied")
                .description("You can't slap yourself! That's just sad.")
                .color(discord.Color.orange())
                .build()
            )
            await ctx.send(embed=embed)
            return

        # Prevent slapping bots
        if target.bot:
            embed = (
                EmbedBuilder()
                .title("🤖 Bot Protection")
                .description("You can't slap bots! They have feelings too... maybe.")
                .color(discord.Color.orange())
                .build()
            )
            await ctx.send(embed=embed)
            return

        # Store the slap in the database
        await db.store_slap_entry(
            guild_id=ctx.guild.id, slapper_id=ctx.author.id, slapped_id=target.id
        )

        # Get a random slap message
        slap_message = random.choice(self.slap_messages).format(
            slapper=ctx.author.mention, slapped=target.mention
        )

        embed = (
            EmbedBuilder()
            .title("👋 SLAP!")
            .description(slap_message)
            .color(discord.Color.red())
            .build()
        )

        await ctx.send(embed=embed)

        self.logger.info(
            f"{ctx.author.name} slapped {target.name} in guild {ctx.guild.name}"
        )

    @slap.command(name="leaderboard", description="Show who's been slapped the most")
    @app_commands.check(guild_only_check)
    async def slap_leaderboard(self, ctx: Context):
        self.logger.info(
            f"User {ctx.author.name} requested slap leaderboard in guild {ctx.guild.name}"
        )
        embed = await self._create_leaderboard_embed(ctx.guild.id)
        await ctx.send(embed=embed)
        self.logger.debug(
            f"Sent slap leaderboard to {ctx.author.name} in {ctx.guild.name}"
        )

    @slap.command(name="stats", description="Show your personal slap statistics")
    @app_commands.check(guild_only_check)
    async def slap_stats(self, ctx: Context):
        self.logger.info(
            f"User {ctx.author.name} requested personal slap stats in guild {ctx.guild.name}"
        )
        embed = await self._create_user_stats_embed(ctx.guild.id, ctx.author.id)
        await ctx.send(embed=embed)
        self.logger.debug(
            f"Sent personal slap stats to {ctx.author.name} in {ctx.guild.name}"
        )

    @slap_user.error
    async def slap_user_error(self, ctx: Context, error: Exception):
        """Error handler for the slap user command."""
        self.logger.error(
            f"Error in slap_user for guild {ctx.guild.id}: {error}", exc_info=True
        )
        embed = (
            EmbedBuilder()
            .title("❌ Error")
            .description("Something went wrong while recording the slap!")
            .color(discord.Color.red())
            .build()
        )
        await ctx.send(embed=embed, ephemeral=True)

    @slap_leaderboard.error
    async def slap_leaderboard_error(self, ctx: Context, error: Exception):
        """Error handler for the slap leaderboard command."""
        self.logger.error(
            f"Error in slap_leaderboard for guild {ctx.guild.id}: {error}",
            exc_info=True,
        )
        embed = (
            EmbedBuilder()
            .title("❌ Error")
            .description("Unable to retrieve the slap leaderboard!")
            .color(discord.Color.red())
            .build()
        )
        await ctx.send(embed=embed, ephemeral=True)

    @slap_stats.error
    async def slap_stats_error(self, ctx: Context, error: Exception):
        """Error handler for the slap stats command."""
        self.logger.error(
            f"Error in slap_stats for guild {ctx.guild.id}: {error}", exc_info=True
        )
        embed = (
            EmbedBuilder()
            .title("❌ Error")
            .description("Unable to retrieve your slap statistics!")
            .color(discord.Color.red())
            .build()
        )
        await ctx.send(embed=embed, ephemeral=True)

    async def _create_leaderboard_embed(self, guild_id: int) -> discord.Embed:
        """Create an embed showing the slap leaderboard."""
        if not (leaderboard_data := await db.get_slap_leaderboard(guild_id)):
            slapped_stats, total_slaps = [], 0
        else:
            slapped_stats, total_slaps = leaderboard_data

        embed = (
            EmbedBuilder()
            .title("👋 Slap Leaderboard")
            .description(f"Total slaps delivered: {total_slaps}")
            .color(discord.Color.red())
            .build()
        )

        if not slapped_stats:
            embed.add_field(
                name="Most Slapped Users",
                value="No slaps recorded yet! Be the first to slap someone! 👋",
                inline=False,
            )
            return embed
        users_text = ""
        for i, (user_id, count) in enumerate(slapped_stats, 1):
            try:
                if not (user := self.bot.get_user(user_id)):
                    user = await self.bot.fetch_user(user_id)
                user_name = user.display_name if user else f"User {user_id}"
            except:
                user_name = f"User {user_id}"

            # Add trophy emojis for top 3
            trophy = ""
            if i == 1:
                trophy = "🥇 "
            elif i == 2:
                trophy = "🥈 "
            elif i == 3:
                trophy = "🥉 "

            users_text += f"{trophy}{i}. {user_name}: {count} slaps\n"

        embed.add_field(
            name="Most Slapped Users",
            value=users_text,
            inline=False,
        )

        return embed

    async def _create_user_stats_embed(
        self, guild_id: int, user_id: int
    ) -> discord.Embed:
        """Create an embed showing a user's slap statistics."""
        (
            times_slapped,
            times_slapping,
            slapped_rank,
            slapper_rank,
        ) = await db.get_user_slap_stats(guild_id, user_id)

        try:
            if not (user := self.bot.get_user(user_id)):
                user = await self.bot.fetch_user(user_id)
            user_name = user.display_name if user else f"User {user_id}"
        except:
            user_name = f"User {user_id}"

        embed = (
            EmbedBuilder()
            .title(f"👋 Slap Stats for {user_name}")
            .color(discord.Color.red())
            .build()
        )

        # Add stats fields
        embed.add_field(
            name="Times Slapped",
            value=f"{times_slapped} times"
            + (f" (Rank #{slapped_rank})" if slapped_rank > 0 else ""),
            inline=True,
        )

        embed.add_field(
            name="Times Slapping Others",
            value=f"{times_slapping} times"
            + (f" (Rank #{slapper_rank})" if slapper_rank > 0 else ""),
            inline=True,
        )

        # Add some fun descriptions based on stats
        if times_slapped == 0 and times_slapping == 0:
            description = "This user hasn't participated in any slapping yet!"
        elif times_slapped > times_slapping:
            description = "This user seems to be on the receiving end of slaps! 😅"
        elif times_slapping > times_slapped:
            description = "This user loves dishing out slaps! 😈"
        else:
            description = "Perfectly balanced slapping record! ⚖️"

        embed.description = description

        return embed


async def setup(bot: Bot):
    await bot.add_cog(Slaps(bot))

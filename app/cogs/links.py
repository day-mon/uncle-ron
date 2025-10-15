import re
from urllib.parse import urlparse

import discord
from discord import app_commands
from discord.ext.commands import Cog, Bot, hybrid_group, Context
from propcache import cached_property

from app.utils.embed_builder import EmbedBuilder
from app.database import db
from app.utils.check_utils import guild_only_check
from app.utils.logger import get_logger


class Links(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.url_pattern = re.compile(r"https?://\S+")

    @cached_property
    def logger(self):
        """Get a logger for this cog."""
        return get_logger(self.__class__.__name__)

    @Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not (urls := self.url_pattern.findall(message.content)):
            return

        for url in urls:
            try:
                parsed_url = urlparse(url)
                if not (hostname := parsed_url.netloc):
                    continue

                guild_name = message.guild.name if message.guild else "DM"
                guild_id = message.guild.id if message.guild else 0

                self.logger.debug(
                    f"Found URL: {url} from {message.author.name} in {guild_name}"
                )

                await db.store_link_entry(
                    guild_id=guild_id,
                    user_id=message.author.id,
                    hostname=hostname,
                    url=url,
                )
                self.logger.info(
                    f"Stored link from {hostname} by user {message.author.name} in {guild_name}"
                )
            except Exception as e:
                self.logger.error(f"Error processing URL {url}: {e}", exc_info=True)

    @hybrid_group(name="links", description="Link tracking commands")
    async def links(self, ctx: Context):
        if ctx.invoked_subcommand is None:
            embed = (
                EmbedBuilder()
                .title("🔗 Link Tracking")
                .description("Use the subcommands to view link statistics")
                .color(discord.Color.blue())
                .add_field(
                    name="Available Commands",
                    value=(
                        "`/links stats` - View server link leaderboard\n"
                        "`/links my` - View your personal link statistics"
                    ),
                    inline=False,
                )
                .build()
            )
            await ctx.send(embed=embed)

    # Using centralized guild_only_check function with app_commands.check()

    @links.command(name="stats", description="Show link leaderboard statistics")
    @app_commands.check(guild_only_check)
    async def links_stats(self, ctx: Context):
        self.logger.info(
            f"User {ctx.author.name} requested link stats in guild {ctx.guild.name}"
        )
        embed = await self._create_leaderboard_embed(ctx.guild.id)
        await ctx.send(embed=embed)
        self.logger.debug(f"Sent link stats to {ctx.author.name} in {ctx.guild.name}")

    @links.command(name="my", description="Show your personal link statistics")
    @app_commands.check(guild_only_check)
    async def links_my(self, ctx: Context):
        self.logger.info(
            f"User {ctx.author.name} requested personal link stats in guild {ctx.guild.name}"
        )
        embed = await self._create_user_stats_embed(ctx.guild.id, ctx.author.id)
        await ctx.send(embed=embed)
        self.logger.debug(
            f"Sent personal link stats to {ctx.author.name} in {ctx.guild.name}"
        )

    async def _create_leaderboard_embed(self, guild_id: int) -> discord.Embed:
        if not (leaderboard_data := await db.get_link_leaderboard(guild_id)):
            user_stats, domain_stats, total_links = [], [], 0
        else:
            user_stats, domain_stats, total_links = leaderboard_data

        embed = (
            EmbedBuilder()
            .title("📊 Link Leaderboard")
            .description(f"Total links shared: {total_links}")
            .color(discord.Color.blue())
            .build()
        )

        users_text = ""
        for i, (user_id, count) in enumerate(user_stats, 1):
            if not (user := self.bot.get_user(user_id)):
                user = await self.bot.fetch_user(user_id)
            user_name = user.display_name if user else f"User {user_id}"
            users_text += f"{i}. {user_name}: {count} links\n"

        embed.add_field(
            name="Top Link Sharers",
            value=users_text if users_text else "No links shared yet",
            inline=False,
        )

        domains_text = ""
        for i, (hostname, count) in enumerate(domain_stats, 1):
            domains_text += f"{i}. {hostname}: {count} links\n"

        embed.add_field(
            name="Top Domains",
            value=domains_text if domains_text else "No domains yet",
            inline=False,
        )

        return embed

    async def _create_user_stats_embed(
        self, guild_id: int, user_id: int
    ) -> discord.Embed:
        if not (user_data := await db.get_user_link_stats(guild_id, user_id)):
            domain_stats, total_links, user_rank = [], 0, 0
        else:
            domain_stats, total_links, user_rank = user_data

        if not (user := self.bot.get_user(user_id)):
            user = await self.bot.fetch_user(user_id)
        user_name = user.display_name if user else f"User {user_id}"

        embed = (
            EmbedBuilder()
            .title(f"🔗 Link Stats for {user_name}")
            .description(f"Rank: #{user_rank} • Total links shared: {total_links}")
            .color(discord.Color.blue())
            .build()
        )

        domains_text = ""
        for i, (hostname, count) in enumerate(domain_stats, 1):
            domains_text += f"{i}. {hostname}: {count} links\n"

        embed.add_field(
            name="Your Top Domains",
            value=domains_text if domains_text else "No links shared yet",
            inline=False,
        )

        return embed


async def setup(bot: Bot):
    await bot.add_cog(Links(bot))

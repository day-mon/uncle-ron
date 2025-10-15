from typing import Any
from zoneinfo import ZoneInfo

import httpx
import asyncio
from datetime import datetime, time, timezone, timedelta
import discord
from discord import app_commands
from discord.ext.commands import Bot, Cog, hybrid_command, Context
from app.utils.check_utils import (
    guild_only_check,
    create_feature_check,
)
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam,
)
from propcache import cached_property
from app.config.app_settings import settings
from app.database import db
from app.constants import QOTD_SYSTEM_PROMPT
from app.models.database import GuildSettings
from app.models.qotd import QOTDResponse
from app.utils import EmbedBuilder, PollBuilder
import json
from app.utils.logger import get_logger


class QOTD(Cog):
    """
    Question of the day

    This cog will post a contriversal though provoking question to the channel every day.

    It will be a poll with 4 options.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.qotd_task = None

    @cached_property
    def logger(self):
        """Get a logger for this cog."""
        return get_logger(self.__class__.__name__)

    @cached_property
    def client(self):
        async def log_request(request):
            self.logger.info(f"🚀 Grok Request: {request.method} {request.url}")
            self.logger.debug(f"Request headers: {dict(request.headers)}")
            if hasattr(request, "content") and request.content:
                self.logger.debug(
                    f"Request body: {request.content.decode('utf-8', errors='ignore')[:500]}..."
                )

        async def log_response(response):
            self.logger.info(
                f"📥 Grok Response: {response.status_code} {response.reason_phrase}"
            )
            self.logger.debug(f"Response headers: {dict(response.headers)}")
            if hasattr(response, "content") and response.content:
                self.logger.debug(
                    f"Response body: {response.content.decode('utf-8', errors='ignore')[:500]}..."
                )

        return AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            http_client=httpx.AsyncClient(
                event_hooks=dict(request=[log_request], response=[log_response]),
            ),
        )

    async def cog_load(self):
        """Start the QOTD scheduler when the cog loads."""
        self.qotd_task = asyncio.create_task(self.qotd_scheduler())
        self.logger.info("📅 QOTD scheduler started")

    async def cog_unload(self):
        """Stop the QOTD scheduler when the cog unloads."""
        if self.qotd_task:
            self.qotd_task.cancel()
            self.logger.info("📅 QOTD scheduler stopped")

    async def qotd_scheduler(self):
        """Schedule QOTD to post at 4 PM EST daily."""
        while True:
            try:
                eastern = ZoneInfo("America/New_York")
                now_est = datetime.now(eastern)

                target_time_est = time(16, 0)
                next_qotd_est = (
                    datetime.combine(now_est.date(), target_time_est, tzinfo=eastern)
                    if now_est.time() < target_time_est
                    else datetime.combine(
                        now_est.date() + timedelta(days=1),
                        target_time_est,
                        tzinfo=eastern,
                    )
                )

                next_qotd_utc = next_qotd_est.astimezone(timezone.utc)
                now_utc = datetime.now(timezone.utc)
                wait_seconds = (next_qotd_utc - now_utc).total_seconds()

                self.logger.info(
                    f"⏰ Next QOTD scheduled for {next_qotd_utc} UTC ({wait_seconds / 3600:.1f} hours)"
                )
                await asyncio.sleep(wait_seconds)

                await self.post_qotd_to_all_guilds()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in QOTD scheduler: {e}")
                await asyncio.sleep(
                    timedelta(hours=1).total_seconds()
                )  # Wait 1 hour before retrying

    async def post_qotd_to_all_guilds(self):
        """Post QOTD to all guilds that have it enabled."""
        for guild in self.bot.guilds:
            try:
                settings = await db.get_guild_settings(guild.id)
                if not settings.settings_json.get("qotd_enabled", False):
                    continue

                if channel := await self.get_qotd_channel(guild, settings):
                    await self.create_and_post_qotd(channel)

            except Exception as e:
                self.logger.error(f"❌ Error posting QOTD to guild {guild.name}: {e}")

    async def get_qotd_channel(self, guild, settings: GuildSettings):
        """Get the configured QOTD channel for a guild."""
        # Check if there's a configured channel
        json_settings = settings.settings_json
        if isinstance(json_settings, str):
            json_settings = json.loads(json_settings)

        if not (configured_channel_id := json_settings.get("qotd_channel_id")) and (
            channel := guild.get_channel(configured_channel_id)
        ):
            return channel

        return guild.text_channels[0] if guild.text_channels else None

    async def generate_qotd(self) -> QOTDResponse:
        """Generate a controversial thought-provoking question with 4 options."""
        response = await self.client.beta.chat.completions.parse(
            model=settings.qotd_model,
            max_tokens=400,
            temperature=0.8,
            response_format=QOTDResponse,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system", content=QOTD_SYSTEM_PROMPT
                ),
                ChatCompletionUserMessageParam(
                    role="user",
                    content="Generate today's Question of the Day with a controversial, thought-provoking question that will spark meaningful discussion.",
                ),
            ],
        )

        result = response.choices[0].message.parsed
        return result

    async def create_and_post_qotd(self, channel):
        """Create and post a QOTD to the specified channel."""
        qotd_data = await self.generate_qotd()
        poll = (
            PollBuilder(
                question=f"🤔 {qotd_data.question}", duration=timedelta(hours=24)
            ).add_answers(
                [
                    qotd_data.option_a,
                    qotd_data.option_b,
                    qotd_data.option_c,
                    qotd_data.option_d,
                ]
            )
        ).build()

        embed = (
            EmbedBuilder()
            .title(f"📊 Question of the Day - {qotd_data.poll_type.title()}")
            .description(f"**{qotd_data.question}**")
            .color(0x00FF00)
            .timestamp()
            .add_fields(
                [
                    dict(
                        name="💭 Why This Question Matters",
                        value=qotd_data.question,
                        inline=False,
                    ),
                    dict(
                        name="🗣️ Expected Discussion",
                        value=qotd_data.expected_discussion,
                        inline=False,
                    ),
                ]
            )
            .footer("Vote in the poll above! Poll closes in 24 hours.")
        ).build()

        await channel.send(embed=embed, poll=poll)
        self.logger.info(
            f"📝 Posted QOTD poll ({qotd_data.poll_type}) to {channel.guild.name}#{channel.name}"
        )

    @hybrid_command(
        name="qotd",
        description="Manually trigger Question of the Day",
    )
    @app_commands.check(guild_only_check)
    @app_commands.check(create_feature_check("qotd_enabled"))
    async def qotd(self, ctx: Context):
        """Manually trigger a Question of the Day."""
        await ctx.defer(ephemeral=True)
        await self.create_and_post_qotd(ctx.channel)
        if ctx.interaction and hasattr(ctx.interaction, "followup"):
            await ctx.interaction.followup.send(
                "✅ Question of the Day posted!", ephemeral=True
            )

    @qotd.error
    async def qotd_error(self, ctx: Context, error: Exception):
        await ctx.send(
            f"❌ QOTD command error: {type(error).__name__}: {error}", ephemeral=True
        )

    @hybrid_command(
        name="qotdchannel",
        description="Set the channel for QOTD posts",
    )
    @app_commands.check(guild_only_check)
    @app_commands.check(create_feature_check("qotd_enabled"))
    @app_commands.describe(
        channel="The channel where QOTD should be posted (leave empty for current channel)"
    )
    async def qotd_channel(
        self, ctx: Context, *, channel: discord.TextChannel | None = None
    ):
        """Set the channel for QOTD posts."""
        # Use current channel if no channel specified
        channel = channel or ctx.channel

        current_settings = await db.get_guild_settings_json(ctx.guild.id)

        # Convert GuildSettings to dictionary
        settings_dict: dict[str, Any] = {}
        if current_settings:
            try:
                settings_dict = current_settings.to_dict()
            except AttributeError:
                try:
                    settings_dict = current_settings.get_settings_dict()
                except (TypeError, ValueError):
                    pass

        # Update the channel ID
        settings_dict["qotd_channel_id"] = channel.id
        await db.update_guild_settings_json(ctx.guild.id, settings_dict)

        await ctx.send(
            f"✅ QOTD will now be posted to {channel.mention}!", ephemeral=True
        )

    @qotd_channel.error
    async def qotd_channel_error(self, ctx: Context, error: Exception):
        await ctx.send(
            f"❌ QOTD channel command error: {type(error).__name__}: {error}",
            ephemeral=True,
        )


async def setup(bot: Bot):
    await bot.add_cog(QOTD(bot))

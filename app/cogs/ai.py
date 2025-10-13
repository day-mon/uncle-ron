import io
import re

import httpx
from discord import (
    Interaction,
    app_commands,
    ChannelType,
    Thread,
    InteractionResponse,
    Webhook,
)
from discord.ext.commands import Cog, Bot, hybrid_command, Context
from dotenv.variables import Literal
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletion,
)
from propcache import cached_property
from pydantic import validate_call, Field
import discord
from app.constants import FACT_CHECK_SYSTEM_PROMPT, FACT_CHECK_USER_PROMPT

from app.config.app_settings import settings
from app.models.ai import FactCheckResponse
from app.database import db
from app.utils.interaction_utils import send
from app.utils.logger import get_logger

logger = get_logger(__name__)


class AI(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.threads = set()

    @cached_property
    def client(self):
        async def log_request(request):
            logger.info(f"🚀 AI Request: {request.method} {request.url}")
            logger.debug(f"Request headers: {dict(request.headers)}")
            if hasattr(request, "content") and request.content:
                logger.debug(
                    f"Request body: {request.content.decode('utf-8', errors='ignore')[:500]}..."
                )

        async def log_response(response):
            logger.info(
                f"📥 AI Response: {response.status_code} {response.reason_phrase}"
            )
            logger.debug(f"Response headers: {dict(response.headers)}")

        return AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
            http_client=httpx.AsyncClient(
                event_hooks=dict(request=[log_request], response=[log_response]),
            ),
        )

    @property
    def message_url_pattern(self):
        return re.compile(
            r"https?://(?:canary\.|ptb\.)?discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
        )

    async def model_autocomplete(self, interaction: Interaction, current: str):
        models = await self.client.models.list()
        return [
            app_commands.Choice(name=m["name"], value=m["name"])
            for m in models["data"]
            if current.lower() in m["name"].lower()
        ][:25]

    async def obtain_thread(
        self, interaction: discord.Interaction, question: str, model: str
    ) -> tuple[discord.Thread, str]:
        channel = interaction.channel

        # If we're already in a thread, use it
        if channel.type in (ChannelType.public_thread, ChannelType.private_thread):
            if stored_model := await db.get_thread_model(channel.id):
                return channel, stored_model

            await db.set_thread_model(interaction.guild.id, channel.id, model)
            return channel, model

        # Create a new thread with the question as the title
        thread_name = (
            f"Question: {question[:50]}…"
            if len(question) > 50
            else f"Question: {question}"
        )
        thread = await channel.create_thread(
            name=thread_name,
            type=ChannelType.public_thread,
            auto_archive_duration=60,
        )

        # Store the model used for this thread
        await db.set_thread_model(interaction.guild.id, thread.id, model)
        return thread, model

    @app_commands.command(
        name="ask",
        description="Ask a question to an AI model and get an answer in a thread.",
    )
    @app_commands.describe(
        question="What do you want to ask?",
        model="The AI model to use",
        temperature="How creative the model should be (0.01–1.0)",
        max_tokens="Maximum number of tokens for the response (1–500)",
    )
    @app_commands.autocomplete(model=model_autocomplete)
    async def ask(
        self,
        interaction: discord.Interaction,
        question: str,
        model: str = settings.default_model,
        temperature: app_commands.Range[float, 0.01, 1.0] = 0.01,
        max_tokens: app_commands.Range[int, 1, 500] = 500,
    ):
        await interaction.response.defer(ephemeral=False)
        
        # Send initial message without creating a thread
        initial_message = await interaction.followup.send(
            f"🚀 Hey {interaction.user.mention}, we're sending your request to the AI with your prompt:\n```\n{question}\n```"
        )
        
        # Get AI response
        oai_response: ChatCompletion = await self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                ChatCompletionUserMessageParam(role="user", content=question),
            ],
        )
        ai_text = oai_response.choices[0].message.content
        
        # Now that we have a response, obtain the thread
        thread, model = await self.obtain_thread(interaction, question, model)
        
        # Send the AI response in the thread
        await thread.send(
            f"💡 **Question from {interaction.user.mention}:**\n```\n{question}\n```\n\n"
            f"🤖 **Answer (using {model}):**\n```\n{ai_text}\n```"
        )
        
        # Edit the original message to point to the thread
        await initial_message.edit(
            content=f"✅ Your question has been answered in {thread.mention}."
        )

    @ask.error
    async def ask_error(self, interaction: discord.Interaction, error: Exception):
        # Try to find the initial message to update it
        try:
            async for message in interaction.channel.history(limit=10):
                if message.author == self.bot.user and message.content.startswith(f"🚀 Hey {interaction.user.mention}"):
                    await message.edit(content=f"❌ Error processing your request: {str(error)}")
                    return
        except:
            pass
            
        # Fallback to sending a new message if we can't find the initial one
        await send(
            interaction=interaction,
            content=f"❌ {type(error).__name__}: {error}",
            ephemeral=True,
        )

    async def _fetch_context_messages(
        self,
        channel: discord.TextChannel,
        before_message: discord.Message,
        count: int,
        user_filter: discord.User = None,
    ) -> list[discord.Message]:
        """
        Fetch context messages before a given message.

        Args:
            channel: The channel to fetch messages from
            before_message: The message to fetch context before
            count: Number of messages to fetch
            user_filter: Optional user to filter messages by

        Returns:
            List of messages in chronological order
        """
        if count <= 0:
            return []

        context_messages = []

        async for msg in channel.history(limit=50, before=before_message):
            if user_filter and msg.author.id != user_filter.id:
                continue

            if msg.author.bot:
                continue

            context_messages.append(msg)

            if len(context_messages) >= count:
                break

        context_messages.reverse()

        return context_messages

    @staticmethod
    def _generate_factcheck_markdown(
        message: discord.Message,
        context_messages: list[discord.Message],
        result,
        user_filter: discord.User = None,
    ) -> str:
        """
        Generate a detailed Markdown report of the fact-check results.

        Args:
            message: The main message being fact-checked
            context_messages: List of context messages
            result: The parsed FactCheckResponse
            user_filter: Optional user filter applied

        Returns:
            Markdown formatted string
        """
        lines = [
            "# Fact Check Report",
            f"\n**Generated:** {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"\n---\n",
            f"## Original Message",
            f"\n**Author:** {message.author.name} (ID: {message.author.id})",
            f"**Timestamp:** {message.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Message ID:** {message.id}",
            f"\n**Content:**\n```\n{message.content}\n```\n",
        ]

        if context_messages:
            lines.append(f"## Context Messages ({len(context_messages)} messages)")
            if user_filter:
                lines.append(f"*Filtered for messages from: {user_filter.name}*\n")

            for idx, msg in enumerate(context_messages, 1):
                lines.append(f"\n### Context Message {idx}")
                lines.append(f"**Author:** {msg.author.name}")
                lines.append(
                    f"**Timestamp:** {msg.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
                lines.append(f"**Content:**\n```\n{msg.content}\n```")

        lines.append("\n---\n")
        lines.append("## Analysis Results\n")

        if result.claims_analyzed:
            lines.append(f"### Claims Analyzed ({len(result.claims_analyzed)} total)\n")

            for idx, claim in enumerate(result.claims_analyzed, 1):
                verdict_emoji = {
                    "TRUE": "✅",
                    "FALSE": "❌",
                    "MISLEADING": "⚠️",
                    "UNVERIFIABLE": "❓",
                }

                lines.append(
                    f"#### Claim {idx}: {verdict_emoji[claim.verdict]} {claim.verdict}"
                )
                lines.append(f"\n**Confidence:** {claim.confidence}")
                lines.append(f"\n**Claim Statement:**")
                lines.append(f"> {claim.claim}")
                lines.append(f"\n**Explanation:**")
                lines.append(claim.explanation)

                if claim.context_needed:
                    lines.append(f"\n**Additional Context:**")
                    lines.append(claim.context_needed)

                lines.append("")  # Empty line for spacing

        lines.append("### Overall Assessment\n")
        lines.append(result.overall_assessment)
        lines.append("")

        flags = []
        if result.requires_current_data:
            flags.append("- 🕐 Requires current data")
        if result.needs_web_search:
            flags.append("- 🌐 Web search recommended")

        if flags:
            lines.append("### Notes\n")
            lines.extend(flags)

        lines.append("\n---\n")
        lines.append(
            "*This report was generated by an AI fact-checking system and should be used as a reference tool.*"
        )
        lines.append(
            "*Always verify important information with authoritative sources.*"
        )

        return "\n".join(lines)

    @staticmethod
    def _build_factcheck_embed(
        interaction: Interaction,
        message: discord.Message,
        context_msgs: list[discord.Message],
        result: "FactCheckResponse",
        user: discord.User | None,
    ) -> discord.Embed:
        """Build the final fact-check results embed."""
        title = "🔍 Fact Check Results"
        if context_msgs:
            title += f" (with {len(context_msgs)} context message{'s' if len(context_msgs) != 1 else ''})"

        embed = discord.Embed(
            title=title,
            description=f"**Message from {message.author.mention}:**\n>>> {message.content[:500]}{'...' if len(message.content) > 500 else ''}",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow(),
        )

        if context_msgs:
            context_info = f"Analyzed {len(context_msgs)} previous message{'s' if len(context_msgs) != 1 else ''}"
            if user:
                context_info += f" from {user.mention}"
            embed.add_field(name="📚 Context", value=context_info, inline=False)

        verdict_emojis = {
            "TRUE": "✅",
            "FALSE": "❌",
            "MISLEADING": "⚠️",
            "UNVERIFIABLE": "❓",
        }

        for idx, claim in enumerate(result.claims_analyzed[:5], start=1):
            emoji = verdict_emojis.get(claim.verdict, "❓")
            confidence = f" ({claim.confidence.lower()} confidence)"
            explanation = claim.explanation[:300]
            if claim.context_needed:
                explanation += f"\n*Context: {claim.context_needed}*"

            embed.add_field(
                name=f"{emoji} {claim.verdict}{confidence}",
                value=f"**Claim:** {claim.claim[:200]}{'...' if len(claim.claim) > 200 else ''}\n{explanation}",
                inline=False,
            )

        if len(result.claims_analyzed) > 5:
            embed.add_field(
                name="📋 Additional Claims",
                value=f"*{len(result.claims_analyzed) - 5} more claims analyzed (truncated)*",
                inline=False,
            )

        embed.add_field(
            name="📊 Overall Assessment",
            value=result.overall_assessment[:1024],
            inline=False,
        )

        flags = []
        if result.requires_current_data:
            flags.append("🕐 Requires current data")
        if result.needs_web_search:
            flags.append("🌐 Web search recommended")
        if flags:
            embed.add_field(name="⚡ Notes", value=" • ".join(flags), inline=False)

        embed.set_footer(
            text=f"Fact-checked by {interaction.user.name}",
            icon_url=interaction.user.display_avatar.url,
        )
        return embed

    async def _obtain_channel(
        self, interaction: Interaction, match: re.Match[str] | None = None
    ):
        if not match:
            return interaction.channel
        guild_id, channel_id, message_id = map(int, match.groups())
        if guild_id != interaction.guild.id:
            raise None
        return interaction.channel.guild.get_channel(channel_id)

    @staticmethod
    def _build_status_message(
        message: discord.Message,
        messages_before: int,
        user: discord.User | None = None,
    ) -> str:
        """Build the status message for fact checking."""
        status_parts = [f"📝 Got message from {message.author.mention}."]

        if messages_before > 1:
            status_parts.append(
                f"Fetching {messages_before - 1} previous messages for context..."
            )

        if user:
            status_parts.append(f"Filtering for messages from {user.mention}.")

        status_parts.append("Beginning fact check... 🤓")

        return " ".join(status_parts)

    @staticmethod
    def factcheck_enabled_check(interaction: discord.Interaction) -> bool:
        """Check if fact check is enabled for the guild."""
        return not interaction.guild or interaction.client.loop.run_until_complete(
            db.is_feature_enabled(interaction.guild.id, "fact_check_enabled")
        )

    @app_commands.command(
        name="factcheck",
        description="Fact checks a message using real time data & LLMs",
    )
    @app_commands.describe(
        message_url="URL of the message to fact check (or reply to a message)",
        messages_before="Number of previous messages to include as context (1-20, default: 1)",
        user="Optional: only include context messages from this specific user",
    )
    async def factcheck(
        self,
        interaction: discord.Interaction,
        message_url: str | None = None,
        messages_before: app_commands.Range[int, 1, 20] = 1,
        user: discord.User | None = None,
    ):
        """
        Fact-check a message with optional context.

        Args:
            interaction: The interaction object
            message_url: Optional message URL to fact check
            messages_before: Number of messages before the referenced message to include as context (1-20, default: 1)
            user: Optional user filter - only include messages from this user in context
        """
        await interaction.response.defer(ephemeral=True)

        if not message_url:
            await send(
                interaction,
                content="❌ Please provide a message URL to fact check.",
                ephemeral=True,
            )
            return

        if not (match := self.message_url_pattern.match(message_url)):
            await send(
                interaction,
                content="❌ Please provide a valid message URL.",
                ephemeral=True,
            )
            return

        channel = await self._obtain_channel(interaction, match=match)
        try:
            message = await channel.fetch_message(int(match.group("message_id")))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            await send(
                interaction=interaction,
                content="❌ Could not fetch the message. Make sure the URL is valid and I have access to that channel.",
                ephemeral=True,
            )
            return

        status_message = self._build_status_message(message, messages_before, user)
        original_message = await interaction.followup.send(status_message)

        context_messages = await self._fetch_context_messages(
            channel=channel,
            before_message=message,
            count=messages_before - 1,
            user_filter=user,
        )

        content = message.content
        if context_messages:
            context_text = "\n\n".join(
                [
                    f"[Context from {msg.author.name} at {msg.created_at.strftime('%Y-%m-%d %H:%M UTC')}]:\n{msg.content}"
                    for msg in context_messages
                ]
            )
            content = f"{context_text}\n\n[Main message to fact-check from {message.author.name}]:\n{message.content}"

        oai_response = await self.client.beta.chat.completions.parse(
            model=settings.fact_check_model,
            max_tokens=1500,
            temperature=0,
            response_format=FactCheckResponse,
            messages=[
                ChatCompletionSystemMessageParam(
                    role="system", content=FACT_CHECK_SYSTEM_PROMPT
                ),
                ChatCompletionUserMessageParam(
                    role="user", content=FACT_CHECK_USER_PROMPT.format(content)
                ),
            ],
        )

        result = oai_response.choices[0].message.parsed

        title = "🔍 Fact Check Results"
        if context_messages:
            title += f" (with {len(context_messages)} context message{'s' if len(context_messages) != 1 else ''})"

        embed = self._build_factcheck_embed(
            interaction=interaction,
            result=result,
            user=user,
            context_msgs=context_messages,
            message=message,
        )

        markdown_content = self._generate_factcheck_markdown(
            message=message,
            context_messages=context_messages,
            result=result,
            user_filter=user,
        )

        file = discord.File(
            fp=io.BytesIO(markdown_content.encode("utf-8")),
            filename="fact_check.md",
        )

        await original_message.edit(content=None, embed=embed, attachments=[file])

    @factcheck.error
    async def factcheck_error(self, ctx: Context, error: Exception):
        """Error handler for the factcheck command."""
        try:
            async for msg in ctx.channel.history(limit=5):
                if msg.author == ctx.bot.user and (
                    "🏃‍♂️" in msg.content or "📝" in msg.content
                ):
                    await msg.edit(content=f"❌ Error during fact-check: {str(error)}")
                    return
        except:
            pass

        await ctx.send(f"❌ Error during fact-check: {str(error)}", ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(AI(bot))

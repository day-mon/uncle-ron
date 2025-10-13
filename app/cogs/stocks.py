import asyncio
import io
import logging
import traceback
from functools import cached_property

import discord
import httpx
import yfinance as yf
import matplotlib.pyplot as plt
from agents import (
    Agent,
    set_tracing_disabled,
    Runner,
    RunConfig,
    RunItemStreamEvent,
    RawResponsesStreamEvent,
    ModelSettings,
)
from discord import app_commands, Interaction
from discord.ext import commands
from openai import AsyncOpenAI

from app.config.app_settings import settings
from app.models.ai import StreamEventResult
from app.utils import EmbedBuilder
from app.utils.ai.tools import (
    get_price,
    get_income_statement,
    get_cash_flow_statement,
    get_balance_sheet,
    web_search,
    get_news,
)
from agents import set_default_openai_client

from app.utils.interaction_utils import send
from app.views.paginated import PaginationView

logger = logging.getLogger(__name__)


class Stocks(commands.GroupCog, name="stock"):
    """Cog providing /stock subcommands for finance data."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cached_property
    def client(self):
        return AsyncOpenAI(
            api_key=settings.openai_api_key,
            http_client=httpx.AsyncClient(
            ),
        )

    @cached_property
    def stock_analysis_agent(self):
        set_default_openai_client(self.client)
        set_tracing_disabled(True)
        return Agent(
            name="Stock Analyst Agent",
            instructions="""
            You are a stock analysis assistant. 
            You can fetch stock prices, financial statements, and web search results 
            to help analyze companies. 
            Use the tools to support your reasoning and provide structured, clear answers.
            """,
            model_settings=ModelSettings(tool_choice="auto"),
            model="o4-mini",
            tools=[
                get_price,
                get_income_statement,
                get_cash_flow_statement,
                get_balance_sheet,
                web_search,
                get_news,
            ],
        )

    @staticmethod
    async def fetch_ticker_info(symbol: str):
        """Fetch ticker info asynchronously using yfinance."""

        def get_info():
            ticker = yf.Ticker(symbol)
            return ticker.info

        return await asyncio.to_thread(get_info)

    @staticmethod
    async def fetch_history(symbol: str, period: str = "1mo", interval: str = "1d"):
        """Fetch historical ticker data asynchronously."""

        def get_history():
            ticker = yf.Ticker(symbol)
            return ticker.history(period=period, interval=interval)

        return await asyncio.to_thread(get_history)

    async def generate_price_chart(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ):
        """Generate and return a BytesIO image buffer of price chart."""
        hist = await self.fetch_history(symbol, period, interval)
        if hist.empty:
            return None

        plt.figure(figsize=(8, 4))
        plt.plot(hist.index, hist["Close"], label=symbol.upper(), linewidth=2)
        plt.title(f"{symbol.upper()} - {period} ({interval})")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        return buf

    @app_commands.command(
        name="price", description="Get the current price and change for a stock."
    )
    async def price(self, interaction: Interaction, symbol: str):
        await interaction.response.defer(thinking=True)
        info = await self.fetch_ticker_info(symbol)
        price = info.get("regularMarketPrice")
        prev_close = info.get("regularMarketPreviousClose")

        if not price:
            embed = EmbedBuilder.error_embed(
                "Not Found", f"No data found for `{symbol}`."
            ).build()
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        change = price - (prev_close or 0)
        pct = (change / prev_close * 100) if prev_close else 0
        color = 0x00FF00 if change >= 0 else 0xFF0000
        sign = "+" if change >= 0 else ""

        embed = (
            EmbedBuilder()
            .title(f"{info.get('shortName', symbol.upper())} ({symbol.upper()})")
            .color(color)
            .add_fields(
                [
                    {"name": "💰 Price", "value": f"${price:,.2f}", "inline": True},
                    {
                        "name": "📈 Change",
                        "value": f"{sign}{change:,.2f} ({sign}{pct:.2f}%)",
                        "inline": True,
                    },
                ]
            )
            .footer("Data from Yahoo Finance")
            .timestamp()
            .build()
        )
        await interaction.followup.send(embed=embed)

    @price.error
    async def price_error(self, interaction: Interaction, error: Exception):
        embed = EmbedBuilder.error_embed(
            "Error", f"Unable to fetch stock info:\n```{error}```"
        ).build()
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="info", description="Get company overview and sector info."
    )
    async def info(self, interaction: Interaction, symbol: str):
        await interaction.response.defer(thinking=True)
        info = await self.fetch_ticker_info(symbol)
        name = info.get("longName") or info.get("shortName") or symbol.upper()
        summary = info.get("longBusinessSummary", "No summary available.")
        sector = info.get("sector", "N/A")
        industry = info.get("industry", "N/A")

        embed = (
            EmbedBuilder()
            .title(name)
            .description(summary[:1024])
            .add_fields(
                [
                    {"name": "🏢 Sector", "value": sector, "inline": True},
                    {"name": "🏭 Industry", "value": industry, "inline": True},
                ]
            )
            .color(0x0099FF)
            .footer("Data from Yahoo Finance")
            .timestamp()
            .build()
        )
        await interaction.followup.send(embed=embed)

    @info.error
    async def info_error(self, interaction: Interaction, error: Exception):
        embed = EmbedBuilder.error_embed(
            "Error", f"Unable to fetch company info:\n```{error}```"
        ).build()
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="chart", description="Show a recent price chart for a stock."
    )
    @app_commands.describe(
        period="Data period (e.g. 1d, 5d, 1mo, 6mo, 1y, 5y, max)",
        interval="Candle interval (e.g. 1d, 1h, 15m)",
    )
    async def chart(
        self,
        interaction: Interaction,
        symbol: str,
        period: str = "1mo",
        interval: str = "1d",
    ):
        await interaction.response.defer(thinking=True)
        chart_buf = await self.generate_price_chart(symbol, period, interval)
        if not chart_buf:
            embed = EmbedBuilder.error_embed(
                "No Data", f"No chart data found for `{symbol}`."
            ).build()
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        embed = (
            EmbedBuilder()
            .title(f"{symbol.upper()} Chart")
            .color(0x0099FF)
            .footer("Data from Yahoo Finance")
            .timestamp()
            .build()
        )

        await interaction.followup.send(
            embed=embed, file=discord.File(chart_buf, filename=f"{symbol}.png")
        )

    @chart.error
    async def chart_error(self, interaction: Interaction, error: Exception):
        embed = EmbedBuilder.error_embed(
            "Error", f"Unable to render chart:\n```{error}```"
        ).build()
        await interaction.followup.send(embed=embed, ephemeral=True)

    async def generate_comparison_chart(
        self, tickers: list[str], period: str = "1mo", interval: str = "1d"
    ):
        """Generate a comparative chart for multiple tickers."""

        async def get_history(symbol: str):
            hist = await self.fetch_history(symbol, period, interval)
            return symbol, hist

        histories = await asyncio.gather(*[get_history(sym) for sym in tickers])
        histories = [(sym, hist) for sym, hist in histories if not hist.empty]

        if not histories:
            return None

        plt.figure(figsize=(8, 4))
        for symbol, hist in histories:
            plt.plot(hist.index, hist["Close"], label=symbol.upper(), linewidth=2)

        plt.title(f"Comparison: {', '.join([s for s, _ in histories])}")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        return buf

    @app_commands.command(
        name="compare", description="Compare up to 4 tickers’ daily performance."
    )
    @app_commands.describe(
        symbol1="First ticker symbol (required)",
        symbol2="Second ticker symbol (required)",
        symbol3="Third ticker symbol (optional)",
        symbol4="Fourth ticker symbol (optional)",
        chart="Include a comparison chart (default: True)",
        period="Chart data period (e.g. 1mo, 6mo, 1y, max)",
        interval="Candle interval (e.g. 1d, 1h, 15m)",
    )
    async def compare(
        self,
        interaction: Interaction,
        symbol1: str,
        symbol2: str,
        symbol3: str | None = None,
        symbol4: str | None = None,
        chart: bool = True,
        period: str = "1mo",
        interval: str = "1d",
    ):
        await interaction.response.defer(thinking=True)

        tickers = [s.upper() for s in [symbol1, symbol2, symbol3, symbol4] if s]
        if not tickers:
            embed = EmbedBuilder.error_embed(
                "Invalid Input", "Please provide at least one ticker symbol."
            ).build()
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        async def fetch(symbol: str):
            info = await self.fetch_ticker_info(symbol)
            price = info.get("regularMarketPrice")
            prev = info.get("regularMarketPreviousClose")
            if not price or not prev:
                return None
            change = price - prev
            pct = change / prev * 100
            return symbol, price, change, pct

        results = await asyncio.gather(*[fetch(sym) for sym in tickers])
        if not (results := [r for r in results if r]):
            embed = EmbedBuilder.error_embed(
                "No Data", "No valid stock data retrieved."
            ).build()
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        fields = []
        for symbol, price, change, pct in results:
            sign = "+" if change >= 0 else ""
            fields.append(
                {
                    "name": symbol,
                    "value": f"${price:,.2f} ({sign}{pct:.2f}%)",
                    "inline": True,
                }
            )

        embed = (
            EmbedBuilder()
            .title("📊 Stock Comparison")
            .color(0x00FFFF)
            .add_fields(fields)
            .footer("Data from Yahoo Finance")
            .timestamp()
            .build()
        )

        if chart:
            if chart_buf := await self.generate_comparison_chart(
                tickers, period, interval
            ):
                await interaction.followup.send(
                    embed=embed, file=discord.File(chart_buf, filename="comparison.png")
                )
                return

        await interaction.followup.send(embed=embed)

    @compare.error
    async def compare_error(self, interaction: Interaction, error: Exception):
        embed = EmbedBuilder.error_embed(
            "Error", f"Unable to compare tickers:\n```{error}```"
        ).build()
        await interaction.followup.send(embed=embed, ephemeral=True)

    @staticmethod
    def build_analysis_embed(
        symbol: str,
        text: str,
        tools_text: str | None = None,
        idx: int | None = None,
        total: int | None = None,
    ) -> discord.Embed:
        embed = discord.Embed(
            title=f"📊 Analysis for {symbol}"
            + (f" ({idx}/{total})" if idx and total else ""),
            description=text,
            color=0x00FFAA,
        )
        if tools_text:
            embed.add_field(
                name="🛠 Tools Used", value=f"```{tools_text}```", inline=False
            )
        return embed

    async def handle_stream_event(
        self,
        event,
    ) -> StreamEventResult:
        """
        Handle a single stream event and return a structured result.
        """
        logger.info(f"Handling stream event: {event}")

        if isinstance(event, RunItemStreamEvent):
            item = event.item
            if item.type == "tool_call_item" and hasattr(item.raw_item, "id"):
                return StreamEventResult(
                    tool_id=item.raw_item.id,
                    tool_name=getattr(item.raw_item, "name", ""),
                    tool_args=getattr(item.raw_item, "arguments", None),
                )

        elif isinstance(event, RawResponsesStreamEvent):
            response_data = getattr(event.data, "delta", None)
            if response_data:
                return StreamEventResult(text_delta=response_data)

            response_obj = getattr(event.data, "response", None)
            if response_obj and hasattr(response_obj, "output"):
                text_chunks = [
                    o.get("text", "") for o in response_obj.output if "text" in o
                ]
                return StreamEventResult(text_delta="".join(text_chunks))

        return StreamEventResult()

    @app_commands.command(
        name="analyze", description="Get AI-powered analysis of a stock."
    )
    @app_commands.describe(
        symbol="Stock ticker symbol to analyze",
        question="Optional specific question about the stock",
        raw="No additional prompting will be added",
    )
    async def analyze(
        self,
        interaction: Interaction,
        symbol: str,
        question: str | None = None,
        raw: bool = False,
    ):
        if raw and not question:
            embed = EmbedBuilder.error_embed(
                title="Incomplete usage",
                description=f"You must provide a question if you are using `raw=True`.",
            ).build()
            await send(
                interaction,
                embed=embed,
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)

        symbol = symbol.upper()

        if question:
            prompt = f"Analyze {symbol} and answer this question: {question}"
        elif raw:
            prompt = f"Symbol: {symbol} \n\n {question}"
        else:
            prompt = f"""Analyze {symbol} stock. Provide:
1. Current price and recent performance
2. Key financial metrics from latest statements
3. Recent news or developments
4. Overall assessment and key insights"""

        status_embed = (
            EmbedBuilder()
            .title(f"🔄 Analyzing {symbol}...")
            .description("Starting analysis...")
            .color(0xFFAA00)
            .build()
        )
        status_msg = await interaction.followup.send(embed=status_embed)

        response = Runner.run_streamed(
            starting_agent=self.stock_analysis_agent, input=prompt
        )

        tool_calls = []
        full_response = ""

        try:
            async for event in response.stream_events():
                result = await self.handle_stream_event(event)
                logger.info(f"Got result: {result.text_delta}")
                full_response += result.text_delta

                if result.tool_id:
                    tool_calls.append(f"{result.tool_name}: {result.tool_args}")

                    tools_text = "\n".join([f"• {tool}" for tool in tool_calls])
                    status_embed = (
                        EmbedBuilder()
                        .title(f"🔄 Analyzing {symbol}...")
                        .description(f"**Tools Used:**\n`{tools_text}`")
                        .color(0xFFAA00)
                        .build()
                    )
                    await status_msg.edit(embed=status_embed)

        except Exception as e:
            await status_msg.delete()
            raise e

        await status_msg.delete()

        analysis_text = (
            full_response or "Analysis completed but no output was generated."
        )

        tools_text = "\n".join([f"• {tool}" for tool in tool_calls]) or "None"

        if len(analysis_text) > 4000:
            chunks = [
                analysis_text[i : i + 4000] for i in range(0, len(analysis_text), 4000)
            ]
            embeds = [
                self.build_analysis_embed(
                    symbol=symbol,
                    text=chunk,
                    tools_text=tools_text if idx == len(chunks) - 1 else None,
                    idx=idx + 1,
                    total=len(chunks),
                )
                for idx, chunk in enumerate(chunks)
            ]
            await interaction.followup.send(
                embed=embeds[0], view=PaginationView(embeds)
            )
        else:
            embed = self.build_analysis_embed(
                text=analysis_text, tools_text=tools_text, symbol=symbol
            )
            await interaction.followup.send(embed=embed)

    @analyze.error
    async def analyze_error(self, interaction: Interaction, error: Exception):
        import traceback

        traceback.print_exc()
        embed = EmbedBuilder.error_embed(
            "Error", f"Unable to perform analysis:\n```{error}```"
        ).build()
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))

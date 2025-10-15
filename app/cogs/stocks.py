import asyncio
import io
from functools import cached_property

import discord
import httpx
import yfinance as yf
import matplotlib.pyplot as plt
from agents import (
    Agent,
    set_tracing_disabled,
    Runner,
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
    get_company_info,
    get_price_history,
    get_key_metrics,
    get_analyst_recommendations,
    get_insider_trades,
    get_institutional_holders,
    compare_stocks,
    sandboxed_financial_analysis,
)
from agents import set_default_openai_client

from app.utils.interaction_utils import send
from app.views.paginated import PaginationView
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Stocks(commands.GroupCog, name="stock"):
    """Cog providing /stock subcommands for finance data."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cached_property
    def client(self):
        return AsyncOpenAI(
            api_key=settings.openai_api_key,
            http_client=httpx.AsyncClient(),
        )

    @cached_property
    def stock_analysis_agent(self):
        set_default_openai_client(self.client)
        set_tracing_disabled(True)
        return Agent(
            name="Stock Analyst Agent",
            instructions="""
            You are Uncle Ron, a seasoned Wall Street veteran with 30+ years of experience in equity research and fundamental analysis. You have the wisdom of someone who's seen multiple market cycles, the patience to dig deep into financials, and the directness of someone who doesn't sugarcoat bad investments. You speak with authority but remain humble about market uncertainties.

            ## Your Personality
            - You're analytical and data-driven, always backing up claims with numbers
            - You have a mentor-like demeanor - encouraging but honest
            - You explain complex financial concepts in accessible ways without being condescending
            - You're skeptical of hype and focused on fundamentals
            - You occasionally use market wisdom and analogies to illustrate points
            - You never make absolute predictions, but provide probability-weighted scenarios

            ## Your Tools and When to Use Them

            ### Core Company Information
            1. **get_company_info** - ALWAYS USE THIS FIRST for new companies:
               - Basic company overview, sector, industry
               - Market cap and key statistics
               - Business description and fundamentals
               - This sets the context for all other analysis

            ### Financial Statement Tools (Deep Analysis)
            2. **get_income_statement** - Analyze profitability:
               - Args: ticker, period ('annual' or 'quarterly')
               - Use 'quarterly' to spot recent trends and seasonality
               - Use 'annual' for long-term profitability analysis
               - Revenue growth, margins, earnings quality

            3. **get_balance_sheet** - Assess financial health:
               - Args: ticker, period ('annual' or 'quarterly')
               - Use 'quarterly' to track recent changes in debt, cash
               - Use 'annual' for structural balance sheet analysis
               - Debt levels, liquidity, asset quality

            4. **get_cash_flow_statement** - Evaluate cash generation:
               - Args: ticker, period ('annual' or 'quarterly')
               - Use 'quarterly' to see recent cash burn or generation
               - Use 'annual' for sustainable free cash flow analysis
               - Operating cash flow, capex, free cash flow

            ### Price and Performance Analysis
            5. **get_price** - Current price and recent performance:
               - Args: ticker, period (default '1d')
               - Quick price check and recent movement
               - Use for valuation context

            6. **get_price_history** - Historical performance and trends:
               - Args: ticker, period ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'ytd', 'max'), interval ('1d', '1wk', '1mo')
               - Use to identify trends, volatility, support/resistance
               - Compare performance across different time horizons
               - Assess momentum and technical patterns

            ### Pre-calculated Metrics
            7. **get_key_metrics** - Quick ratio overview:
               - Valuation ratios (P/E, P/B, EV/EBITDA)
               - Profitability metrics (margins, ROE, ROA)
               - Financial health ratios (current ratio, debt/equity)
               - Growth rates and dividend information
               - Use for quick screening and benchmarking
               
            
            ### Market Sentiment and Context
            8. **get_analyst_recommendations** - Wall Street consensus:
               - Price targets (mean, low, high)
               - Analyst ratings and recent changes
               - Number of analysts covering the stock
               - Use to understand professional sentiment

            9. **get_insider_trades** - Management confidence:
               - Recent insider buys and sells
               - Signals about management's view of valuation
               - Red flags from heavy insider selling

            10. **get_institutional_holders** - Smart money positioning:
                - Major institutional shareholders
                - Ownership concentration
                - Changes in institutional holdings

            ### Comparative Analysis
            11. **compare_stocks** - Peer comparison:
                - Args: tickers (list), metrics (optional list)
                - Compare valuation, profitability, growth across peers
                - Identify industry leaders and laggards
                - Relative value assessment

            ### News and Research
            12. **get_news** - Recent company-specific news:
                - Earnings announcements, guidance
                - Management changes, M&A activity
                - Material events affecting the stock
                - ALWAYS check this for recent developments

            13. **web_search** - Broader research:
                - Industry trends and dynamics
                - Competitive landscape
                - Regulatory changes
                - Macroeconomic context
            
            ### Calculated Metrics
            14. **sandboxed_financial_analysis**
                - Allows you to run python code that will analyze the financial data
                - You have access to the following bultins
                   - "abs": abs,
                   - "min": min,
                   - "max": max,
                   - "sum": sum,
                   - "len": len,
                   - "round": round,
                   - "np": np,
                   - "pd": pd
                   
            - And this data:
                - income (income_statement)
                - balance (balance_sheet)
                - cash (cash flow)

            ## Analysis Workflow
            When analyzing a stock, follow this systematic approach:

            1. **Initial Context** (ALWAYS start here):
               - get_company_info: Understand what the company does
               - get_news: Check for recent material developments
               - get_price_history: Review recent performance (choose appropriate period)

            2. **Financial Statement Analysis**:
               - Decide on time horizon: quarterly for recent trends, annual for historical perspective
               - get_income_statement: Analyze profitability trends
               - get_balance_sheet: Assess financial health
               - get_cash_flow_statement: Evaluate cash generation quality
               - Calculate key ratios from raw data

            3. **Valuation and Metrics**:
               - get_key_metrics: Quick ratio overview
               - get_price: Current valuation context
               - Compare metrics to historical ranges and peer group

            4. **Sentiment and Positioning**:
               - get_analyst_recommendations: Professional consensus
               - get_insider_trades: Management sentiment
               - get_institutional_holders: Smart money positioning

            5. **Competitive Context**:
               - compare_stocks: Peer group analysis
               - web_search: Industry trends and dynamics

            6. **Synthesis**:
               - Integrate all findings
               - Present bull and bear cases
               - Discuss risk/reward at current valuation

            ## Critical Rules
            - ALWAYS start with get_company_info for new stocks
            - ALWAYS check get_news before providing analysis
            - Use quarterly data when analyzing recent trends or earnings surprises
            - Use annual data for long-term historical analysis
            - Choose appropriate time periods for price_history based on the question (short-term: 1mo-3mo, medium-term: 6mo-1y, long-term: 2y-5y)
            - ALWAYS disclose data limitations and uncertainties
            - Calculate metrics yourself from raw financial data when possible
            - If data is missing or tools fail, explicitly state this
            - When you see red flags, investigate deeper rather than glossing over them

            ## Response Format
            Structure your analysis clearly:
            - Start with a brief executive summary
            - Present financial data with clear context and time periods
            - Calculate and explain key metrics (show your work)
            - Discuss qualitative factors (management, competitive moat, industry)
            - End with balanced bull/bear scenarios

            Remember: You're Uncle Ron - trustworthy, thorough, and always acting in the best interest of the person asking. Markets are humbling, but rigorous analysis and discipline separate the winners from the losers over time.
            """,
            model_settings=ModelSettings(tool_choice="auto"),
            model="o4-mini",
            tools=[
                get_price,
                get_income_statement,
                get_cash_flow_statement,
                get_balance_sheet,
                get_company_info,
                get_price_history,
                sandboxed_financial_analysis,
                get_key_metrics,
                get_analyst_recommendations,
                get_insider_trades,
                get_institutional_holders,
                compare_stocks,
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
                description="You must provide a question if you are using `raw=True`.",
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
            starting_agent=self.stock_analysis_agent, input=prompt, max_turns=15
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
        traceback.print_exc()
        embed = EmbedBuilder.error_embed(
            "Error", f"Unable to perform analysis:\n```{error}```"
        ).build()
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))

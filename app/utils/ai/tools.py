import asyncio
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf
from agents import function_tool
from duckduckgo_search import DDGS




def _safe_financial_analysis(
    analysis_code: str,
    *,
    income_statement: dict[str, Any] | None = None,
    balance_sheet:  dict[str, Any] | None = None,
    cash_flow:  dict[str, Any] | None = None,
) -> dict:
    """
    Run dynamic financial analysis safely using a sandboxed environment.

    Args:
        income_statement: dict from get_income_statement
        balance_sheet: dict from get_balance_sheet
        cash_flow: dict from get_cash_flow_statement
        analysis_code: Python code string to execute using `income`, `balance`, `cash`
                       Must assign results to a variable named `output`.
    Returns:
        dict with results or error
    """

    income = pd.DataFrame(income_statement["data"]).T if income_statement else pd.DataFrame()
    balance = pd.DataFrame(balance_sheet["data"]).T if balance_sheet else pd.DataFrame()
    cash = pd.DataFrame(cash_flow["data"]).T if cash_flow else pd.DataFrame()

    income = income.apply(pd.to_numeric, errors='coerce')
    balance = balance.apply(pd.to_numeric, errors='coerce')
    cash = cash.apply(pd.to_numeric, errors='coerce')

    safe_builtins = {
        "abs": abs,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "round": round,
    }

    safe_locals = {
        "income": income,
        "balance": balance,
        "cash": cash,
        "np": np,
        "pd": pd,
        "output": {}
    }

    try:
        # Execute code safely
        exec(analysis_code, {"__builtins__": safe_builtins}, safe_locals)
        return safe_locals.get("output", {})
    except Exception as e:
        return {"error": f"Analysis failed: {e}"}

def _fetch_price(ticker: str, period: str = "1d"):
    """Fetch current or recent price data."""
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    if data.empty:
        return {"error": f"Could not fetch price for {ticker}"}
    price = data["Close"].iloc[-1]
    return {"ticker": ticker, "price": round(float(price), 2), "period": period}


def _fetch_income_statement(ticker: str, period: str = "annual"):
    """Fetch income statement - annual or quarterly."""
    stock = yf.Ticker(ticker)
    df = stock.income_stmt if period == "annual" else stock.quarterly_income_stmt
    if df is None or df.empty:
        return {"error": f"Could not fetch {period} income statement for {ticker}"}
    return {"ticker": ticker, "period": period, "data": df.to_dict()}


def _fetch_cash_flow(ticker: str, period: str = "annual") -> dict[str, Any]:
    """Fetch cash flow statement - annual or quarterly."""
    stock = yf.Ticker(ticker)
    df = stock.cashflow if period == "annual" else stock.quarterly_cashflow
    if df is None or df.empty:
        return {"error": f"Could not fetch {period} cash flow statement for {ticker}"}
    return {"ticker": ticker, "period": period, "data": df.to_dict()}


def _fetch_balance_sheet(ticker: str, period: str = "annual"):
    """Fetch balance sheet - annual or quarterly."""
    stock = yf.Ticker(ticker)
    df = stock.balance_sheet if period == "annual" else stock.quarterly_balance_sheet
    if df is None or df.empty:
        return {"error": f"Could not fetch {period} balance sheet for {ticker}"}
    return {"ticker": ticker, "period": period, "data": df.to_dict()}


def _fetch_company_info(ticker: str):
    """Fetch comprehensive company information."""
    stock = yf.Ticker(ticker)
    info = stock.info
    if not info:
        return {"error": f"Could not fetch info for {ticker}"}

    return {
        "ticker": ticker,
        "company_name": info.get("longName"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "52_week_high": info.get("fiftyTwoWeekHigh"),
        "52_week_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
        "description": info.get("longBusinessSummary"),
        "website": info.get("website"),
        "employees": info.get("fullTimeEmployees"),
        "country": info.get("country"),
        "city": info.get("city"),
    }


def _fetch_price_history(ticker: str, period: str = "1y", interval: str = "1d"):
    """Fetch historical price data with flexible periods."""
    stock = yf.Ticker(ticker)
    df = stock.history(period=period, interval=interval)
    if df.empty:
        return {"error": f"Could not fetch price history for {ticker}"}

    return {
        "ticker": ticker,
        "period": period,
        "interval": interval,
        "data": df.to_dict(),
        "summary": {
            "start_date": str(df.index[0]),
            "end_date": str(df.index[-1]),
            "start_price": float(df["Close"].iloc[0]),
            "end_price": float(df["Close"].iloc[-1]),
            "high": float(df["High"].max()),
            "low": float(df["Low"].min()),
            "avg_volume": float(df["Volume"].mean()),
            "return_pct": round(((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1) * 100, 2),
            "volatility": round(float(df["Close"].pct_change().std() * 100), 2),
        }
    }


def _fetch_key_metrics(ticker: str):
    """Fetch pre-calculated financial metrics and ratios."""
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        "ticker": ticker,
        "valuation": {
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "peg_ratio": info.get("pegRatio"),
            "price_to_book": info.get("priceToBook"),
            "price_to_sales": info.get("priceToSalesTrailing12Months"),
            "ev_to_revenue": info.get("enterpriseToRevenue"),
            "ev_to_ebitda": info.get("enterpriseToEbitda"),
            "market_cap": info.get("marketCap"),
            "enterprise_value": info.get("enterpriseValue"),
        },
        "profitability": {
            "profit_margin": info.get("profitMargins"),
            "operating_margin": info.get("operatingMargins"),
            "gross_margin": info.get("grossMargins"),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            "roic": info.get("returnOnCapital"),
        },
        "financial_health": {
            "current_ratio": info.get("currentRatio"),
            "quick_ratio": info.get("quickRatio"),
            "debt_to_equity": info.get("debtToEquity"),
            "total_debt": info.get("totalDebt"),
            "total_cash": info.get("totalCash"),
            "free_cash_flow": info.get("freeCashflow"),
        },
        "growth": {
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
        },
        "dividend": {
            "dividend_rate": info.get("dividendRate"),
            "dividend_yield": info.get("dividendYield"),
            "payout_ratio": info.get("payoutRatio"),
            "five_year_avg_dividend_yield": info.get("fiveYearAvgDividendYield"),
        }
    }


def _fetch_analyst_recommendations(ticker: str):
    """Fetch analyst recommendations and price targets."""
    stock = yf.Ticker(ticker)
    recommendations = stock.recommendations
    info = stock.info

    result = {
        "ticker": ticker,
        "target_price": {
            "current_price": info.get("currentPrice"),
            "mean_target": info.get("targetMeanPrice"),
            "low_target": info.get("targetLowPrice"),
            "high_target": info.get("targetHighPrice"),
            "median_target": info.get("targetMedianPrice"),
        },
        "recommendation": info.get("recommendationKey"),
        "num_analysts": info.get("numberOfAnalystOpinions"),
    }

    if recommendations is not None and not recommendations.empty:
        recent = recommendations.tail(20)
        result["recent_recommendations"] = recent.to_dict()

    return result


def _fetch_insider_trades(ticker: str):
    """Fetch recent insider trading activity."""
    stock = yf.Ticker(ticker)
    insider_trades = stock.insider_transactions

    if insider_trades is None or insider_trades.empty:
        return {"error": f"No insider trading data available for {ticker}"}

    recent = insider_trades.head(30)

    return {
        "ticker": ticker,
        "recent_trades": recent.to_dict(),
        "trade_count": len(insider_trades),
    }


def _fetch_institutional_holders(ticker: str):
    """Fetch major institutional holders and ownership data."""
    stock = yf.Ticker(ticker)
    institutional = stock.institutional_holders
    major = stock.major_holders

    result = {"ticker": ticker}

    if institutional is not None and not institutional.empty:
        result["top_institutions"] = institutional.head(15).to_dict()

    if major is not None and not major.empty:
        result["ownership_summary"] = major.to_dict()

    return result if len(result) > 1 else {"error": f"No holder data for {ticker}"}


def _compare_stocks(tickers: list[str], metrics: list[str] = None):
    """Compare key metrics across multiple stocks."""
    if metrics is None:
        metrics = [
            "marketCap", "trailingPE", "forwardPE", "priceToBook",
            "profitMargins", "operatingMargins", "returnOnEquity",
            "revenueGrowth", "earningsGrowth", "debtToEquity",
            "currentRatio", "freeCashflow", "dividendYield"
        ]

    comparison = {}
    for ticker in tickers:
        ticker = ticker.upper()
        stock = yf.Ticker(ticker)
        info = stock.info
        comparison[ticker] = {
            "company_name": info.get("longName"),
            "sector": info.get("sector"),
            **{metric: info.get(metric) for metric in metrics}
        }

    return {"comparison": comparison, "metrics_compared": metrics}


def _web_search(query: str, max_results: int = 5):
    """Perform a web search."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                {"title": r["title"], "url": r["href"], "snippet": r["body"]}
            )
    return results


def _search_news(query: str, max_results: int = 5):
    """Search for recent news articles."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.news(query, max_results=max_results):
            results.append(
                {
                    "title": r.get("title"),
                    "url": r.get("url"),
                    "source": r.get("source"),
                    "date": r.get("date"),
                    "snippet": r.get("body"),
                }
            )
    return results


# ============================================================================
# PUBLIC TOOL FUNCTIONS
# ============================================================================


@function_tool
async def get_price(ticker: str, period: str = "1d") -> dict:
    """
    Get the latest price for a given stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
        period: Time period for price data. Options: '1d', '5d', '1mo', '3mo', '6mo', '1y'
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_price, ticker, period)


@function_tool
async def get_income_statement(ticker: str, period: str = "annual") -> dict:
    """
    Fetch income statement for the ticker.

    Args:
        ticker: Stock ticker symbol
        period: 'annual' for yearly data or 'quarterly' for quarterly data
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_income_statement, ticker, period)


@function_tool
async def get_cash_flow_statement(ticker: str, period: str = "annual") -> dict:
    """
    Fetch cash flow statement for the ticker.

    Args:
        ticker: Stock ticker symbol
        period: 'annual' for yearly data or 'quarterly' for quarterly data
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_cash_flow, ticker, period)


@function_tool
async def get_balance_sheet(ticker: str, period: str = "annual") -> dict:
    """
    Fetch balance sheet for the ticker.

    Args:
        ticker: Stock ticker symbol
        period: 'annual' for yearly data or 'quarterly' for quarterly data
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_balance_sheet, ticker, period)


@function_tool
async def get_company_info(ticker: str) -> dict:
    """
    Get comprehensive company information including sector, industry, market cap,
    PE ratio, dividend yield, beta, and business description.

    Args:
        ticker: Stock ticker symbol
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_company_info, ticker)


@function_tool
async def get_price_history(ticker: str, period: str = "1y", interval: str = "1d") -> dict:
    """
    Get historical price data for technical and trend analysis.

    Args:
        ticker: Stock ticker symbol
        period: Time period. Options: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        interval: Data interval. Options: '1m', '5m', '15m', '30m', '1h', '1d', '1wk', '1mo'
                  Note: Intraday data (1m-1h) only available for last 60 days
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_price_history, ticker, period, interval)


@function_tool
async def get_key_metrics(ticker: str) -> dict:
    """
    Get key financial metrics and ratios pre-calculated by yfinance.
    Includes valuation, profitability, financial health, growth, and dividend metrics.

    Args:
        ticker: Stock ticker symbol
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_key_metrics, ticker)


@function_tool
async def get_analyst_recommendations(ticker: str) -> dict:
    """
    Get analyst recommendations and price targets for the stock.

    Args:
        ticker: Stock ticker symbol
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_analyst_recommendations, ticker)


@function_tool
async def get_insider_trades(ticker: str) -> dict:
    """
    Get recent insider trading activity (buys/sells by executives and large shareholders).

    Args:
        ticker: Stock ticker symbol
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_insider_trades, ticker)


@function_tool
async def get_institutional_holders(ticker: str) -> dict:
    """
    Get major institutional holders and their positions.

    Args:
        ticker: Stock ticker symbol
    """
    ticker = ticker.upper()
    return await asyncio.to_thread(_fetch_institutional_holders, ticker)


@function_tool
async def compare_stocks(tickers: list[str], metrics: list[str] = None) -> dict:
    """
    Compare key metrics across multiple stocks for peer analysis.

    Args:
        tickers: List of ticker symbols to compare (e.g., ['AAPL', 'MSFT', 'GOOGL'])
        metrics: Optional list of specific metrics to compare. If None, uses default set.
                 Available metrics: 'marketCap', 'trailingPE', 'forwardPE', 'priceToBook',
                 'profitMargins', 'operatingMargins', 'returnOnEquity', 'revenueGrowth',
                 'earningsGrowth', 'debtToEquity', 'currentRatio', 'freeCashflow', 'dividendYield'
    """
    tickers = [t.upper() for t in tickers]
    return await asyncio.to_thread(_compare_stocks, tickers, metrics)


@function_tool
async def web_search(query: str, max_results: int = 5) -> list:
    """
    Perform a web search for recent information about companies or industries.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
    """
    return await asyncio.to_thread(_web_search, query, max_results)


@function_tool
async def get_news(query: str, max_results: int = 5) -> list:
    """
    Search for recent company news articles.

    Args:
        query: Search query (typically company name or ticker)
        max_results: Maximum number of news articles to return (default: 5)
    """
    return await asyncio.to_thread(_search_news, query, max_results)

@function_tool
async def sandboxed_financial_analysis(
    ticker: str,
    analysis_code: str
) -> dict:
    """
    Run sandboxed dynamic financial analysis. The agent can provide custom
    Python code using `income`, `balance`, `cash` DataFrames. Must assign results to `output`.
    """

    ticker = ticker.upper()

    income_statement: dict[str, Any] = await asyncio.to_thread(_fetch_income_statement, ticker, "annual")
    balance_sheet: dict[str, Any] = await asyncio.to_thread(_fetch_balance_sheet, ticker, "annual")
    cash_flow: dict[str, Any] = await asyncio.to_thread(_fetch_cash_flow, ticker, "annual")

    return await asyncio.to_thread(
        _safe_financial_analysis,
        analysis_code,
        income_statement,
        balance_sheet,
        cash_flow,
    )
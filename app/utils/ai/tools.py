import asyncio
import yfinance as yf
from agents import function_tool
from duckduckgo_search import DDGS


@function_tool
async def get_price(ticker: str) -> dict:
    """
    Get the latest price for a given stock ticker asynchronously.
    """
    ticker = ticker.upper()

    def fetch_price():
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty:
            return {"error": f"Could not fetch price for {ticker}"}
        price = data["Close"].iloc[-1]
        return {"ticker": ticker, "price": round(float(price), 2)}

    return await asyncio.to_thread(fetch_price)


@function_tool
async def get_income_statement(ticker: str) -> dict:
    """
    Fetch the most recent annual income statement for the ticker asynchronously.
    """
    ticker = ticker.upper()

    def fetch_income_statement():
        stock = yf.Ticker(ticker)
        df = stock.income_stmt
        if df is None or df.empty:
            return {"error": f"Could not fetch income statement for {ticker}"}
        return df.to_dict()

    return await asyncio.to_thread(fetch_income_statement)


@function_tool
async def get_cash_flow_statement(ticker: str) -> dict:
    """
    Fetch the most recent annual cash flow statement for the ticker asynchronously.
    """
    ticker = ticker.upper()

    def fetch_cash_flow():
        stock = yf.Ticker(ticker)
        df = stock.cashflow
        if df is None or df.empty:
            return {"error": f"Could not fetch cash flow statement for {ticker}"}
        return df.to_dict()

    return await asyncio.to_thread(fetch_cash_flow)


@function_tool
async def get_balance_sheet(ticker: str) -> dict:
    """
    Fetch the most recent annual balance sheet for the ticker asynchronously.
    """
    ticker = ticker.upper()

    def fetch_balance_sheet():
        stock = yf.Ticker(ticker)
        df = stock.balance_sheet
        if df is None or df.empty:
            return {"error": f"Could not fetch balance sheet for {ticker}"}
        return df.to_dict()

    return await asyncio.to_thread(fetch_balance_sheet)


@function_tool
async def web_search(query: str, max_results: int = 5) -> list:
    """
    Perform a web search for recent info about the company asynchronously.
    """

    def search():
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {"title": r["title"], "url": r["href"], "snippet": r["body"]}
                )
        return results

    return await asyncio.to_thread(search)


@function_tool
async def get_news(query: str, max_results: int = 5) -> list:
    """
    Search for recent company news articles asynchronously.
    """

    def search_news():
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

    return await asyncio.to_thread(search_news)

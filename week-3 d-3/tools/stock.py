"""
📈 Stock Price Tool (Stretch Goal)

Gets real-time stock prices and market data.

Uses yfinance (free, no API key) or finnhub.io free tier.
"""

import os
from typing import Optional

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


def get_stock_price(symbol: str) -> str:
    """
    Get current stock price and info for a ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA', 'NVDA')

    Returns:
        Formatted stock information string
    """
    if not HAS_YFINANCE:
        try:
            return _fetch_stock_finnhub(symbol)
        except Exception:
            return (
                "❌ yfinance package not installed.\n"
                "Run: pip install yfinance"
            )

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}

        # Get current price
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        change = info.get("regularMarketChange")
        change_pct = info.get("regularMarketChangePercent")

        # Additional info
        name = info.get("longName") or info.get("shortName") or symbol.upper()
        high = info.get("regularMarketDayHigh") or info.get("dayHigh")
        low = info.get("regularMarketDayLow") or info.get("dayLow")
        volume = info.get("regularMarketVolume") or info.get("volume")
        market_cap = info.get("marketCap")
        pe_ratio = info.get("trailingPE")

        # Format volume / market cap
        def fmt_big(n):
            if n is None:
                return "N/A"
            if n >= 1_000_000_000_000:
                return f"${n/1_000_000_000_000:.2f}T"
            if n >= 1_000_000_000:
                return f"${n/1_000_000_000:.2f}B"
            if n >= 1_000_000:
                return f"${n/1_000_000:.2f}M"
            return f"{n:,}"

        lines = [
            f"📈 {name} ({symbol.upper()})",
        ]

        if price:
            change_str = ""
            if change is not None and change_pct is not None:
                arrow = "▲" if change >= 0 else "▼"
                change_str = f" ({arrow} {abs(change):.2f} / {abs(change_pct):.2f}%)"
            lines.append(f"   💰 ${price:.2f}{change_str}")

        if high and low:
            lines.append(f"   📊 Day Range: ${low:.2f} – ${high:.2f}")
        if volume:
            lines.append(f"   📦 Volume: {volume:,}")
        if market_cap:
            lines.append(f"   🏢 Market Cap: {fmt_big(market_cap)}")
        if pe_ratio:
            lines.append(f"   📐 P/E Ratio: {pe_ratio:.2f}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Stock price error for {symbol}: {e}"


def _fetch_stock_finnhub(symbol: str) -> str:
    """Fallback: fetch stock quote using finnhub.io (limited free tier)."""
    api_key = os.getenv("FINNHUB_API_KEY", "")
    if not api_key:
        return f"❌ No API key for stock data. Install yfinance or set FINNHUB_API_KEY."

    import requests

    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        price = data.get("c")
        change = data.get("d")
        change_pct = data.get("dp")
        high = data.get("h")
        low = data.get("l")

        lines = [f"📈 {symbol.upper()}"]
        if price:
            change_str = ""
            if change is not None and change_pct is not None:
                arrow = "▲" if change >= 0 else "▼"
                change_str = f" ({arrow} {abs(change):.2f} / {abs(change_pct):.2f}%)"
            lines.append(f"   💰 ${price:.2f}{change_str}")
        if high and low:
            lines.append(f"   📊 Day Range: ${low:.2f} – ${high:.2f}")

        return "\n".join(lines)

    except Exception as e:
        return f"❌ Finnhub error for {symbol}: {e}"


# ──────────────────────────────────────────────────────────────
# JSON Schema for tool calling
# ──────────────────────────────────────────────────────────────

SCHEMA = {
    "name": "get_stock_price",
    "description": "Get current stock price, change, day range, volume, and market cap for any publicly traded company",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'TSLA', 'NVDA', 'MSFT')",
            },
        },
        "required": ["symbol"],
    },
}


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("📈 Stock Tool Test")
    print("-" * 40)
    result = get_stock_price("AAPL")
    print(result)
    print()
    result2 = get_stock_price("NVDA")
    print(result2)

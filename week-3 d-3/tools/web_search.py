"""
🔍 Web Search Tool

Searches the web using DuckDuckGo (free, no API key needed).

Part 4 of Day 13 — Gives the agent live internet access.
"""

import warnings
from typing import Optional

# Suppress deprecation warning about package rename
warnings.filterwarnings("ignore", message=".*renamed to `ddgs`.*")

# Try new package name first (ddgs), fall back to old (duckduckgo-search)
try:
    from ddgs import DDGS
    HAS_DUCKDUCKGO = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        HAS_DUCKDUCKGO = True
    except ImportError:
        HAS_DUCKDUCKGO = False


def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web using DuckDuckGo.

    Args:
        query: The search query string
        max_results: Maximum number of results to return (default 5)

    Returns:
        Formatted string of search results, or error message
    """
    if not HAS_DUCKDUCKGO:
        return (
            "❌ DuckDuckGo search package not installed.\n"
            "Run: pip install ddgs  (or: pip install duckduckgo-search)"
        )

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for: '{query}'"

        output = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            snippet = r.get("body", "") or r.get("snippet", "No snippet")
            link = r.get("href", r.get("link", "No link"))
            output.append(
                f"{i}. {title}\n"
                f"   {snippet[:200]}{'…' if len(snippet) > 200 else ''}\n"
                f"   🔗 {link}"
            )

        return "\n\n".join(output)

    except Exception as e:
        return f"❌ Web search error: {e}"


# ──────────────────────────────────────────────────────────────
# JSON Schema for tool calling
# ──────────────────────────────────────────────────────────────

SCHEMA = {
    "name": "search_web",
    "description": "Search the internet for current information, news, or any topic. Use this when you need up-to-date data.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query string (e.g., 'latest NVIDIA stock price')",
            },
            "max_results": {
                "type": "integer",
                "description": "Number of search results to return (1–10)",
                "default": 5,
            },
        },
        "required": ["query"],
    },
}


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🔍 Web Search Tool Test")
    print("-" * 40)
    result = search_web("latest AI news 2026", max_results=3)
    print(result)

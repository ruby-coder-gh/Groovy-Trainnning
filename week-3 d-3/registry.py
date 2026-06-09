"""
🗂️ Tool Registry

Maps tool names to their implementations and schemas.

Part 3 + Part 6 of Day 13 — The registry is what the agent loop
uses to look up and execute tools dynamically.
"""

from typing import Any, Dict, Callable

# ──────────────────────────────────────────────────────────────
# Import all tool implementations
# ──────────────────────────────────────────────────────────────

import tools.calculator as calc_mod
import tools.web_search as search_mod
import tools.slack as slack_mod
import tools.weather as weather_mod
import tools.stock as stock_mod
import tools.database as db_mod
import tools.file_reader as file_mod

# ──────────────────────────────────────────────────────────────
# Registry: tool_name → (function, schema)
# ──────────────────────────────────────────────────────────────

REGISTRY: Dict[str, Dict[str, Any]] = {
    # ── Core Tools (Day 13 required) ──────────────────────────
    "calculator": {
        "function": calc_mod.calculate,
        "schema": calc_mod.SCHEMA,
    },
    "search_web": {
        "function": search_mod.search_web,
        "schema": search_mod.SCHEMA,
    },
    "send_slack": {
        "function": slack_mod.send_slack,
        "schema": slack_mod.SCHEMA,
    },
    # ── Stretch Goals ─────────────────────────────────────────
    "get_weather": {
        "function": weather_mod.get_weather,
        "schema": weather_mod.SCHEMA,
    },
    "get_stock_price": {
        "function": stock_mod.get_stock_price,
        "schema": stock_mod.SCHEMA,
    },
    "query_database": {
        "function": db_mod.query_database,
        "schema": db_mod.SCHEMA,
    },
    "read_file": {
        "function": file_mod.read_file,
        "schema": file_mod.SCHEMA,
    },
}


# ──────────────────────────────────────────────────────────────
# Convenience functions
# ──────────────────────────────────────────────────────────────


def get_tool(name: str) -> Callable:
    """Get a tool function by name."""
    entry = REGISTRY.get(name)
    if entry is None:
        valid = ", ".join(REGISTRY.keys())
        raise KeyError(f"Unknown tool '{name}'. Valid tools: {valid}")
    return entry["function"]


def get_schema(name: str) -> Dict:
    """Get a tool's JSON schema by name."""
    entry = REGISTRY.get(name)
    if entry is None:
        valid = ", ".join(REGISTRY.keys())
        raise KeyError(f"Unknown tool '{name}'. Valid tools: {valid}")
    return entry["schema"]


def list_tools() -> str:
    """Return a formatted list of all registered tools."""
    lines = ["🗂️  Registered Tools:", "─" * 50]
    for name, entry in REGISTRY.items():
        schema = entry["schema"]
        desc = schema.get("description", "No description")
        params = schema.get("parameters", {}).get("properties", {})
        required = schema.get("parameters", {}).get("required", [])
        param_list = ", ".join(
            f"{k}" + ("*" if k in required else "")
            for k in params
        )
        lines.append(f"  • {name}: {desc}")
        if param_list:
            lines.append(f"    Args: {param_list}")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(list_tools())

    print("\n\n🔧 Testing tool lookups:")
    print("-" * 40)

    # Test calculator
    calc = get_tool("calculator")
    result = calc(10, 20, "multiply")
    print(f"  calculator(10, 20, 'multiply') → {result}")

    # Test search
    search = get_tool("search_web")
    result = search("Python agent tutorial", max_results=2)
    print(f"  search_web → {result[:80]}...")

    # Test slack
    slack = get_tool("send_slack")
    result = slack("Test message")
    print(f"  send_slack → {result[:80]}...")

    # Test weather
    weather = get_tool("get_weather")
    result = weather("Tokyo")
    print(f"  get_weather → {result[:80]}...")

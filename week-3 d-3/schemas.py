"""
📋 JSON Schemas for All Tools

Part 2 + Part 7 of Day 13 — These schemas are what we pass to
OpenAI/Cohere so the LLM knows what tools are available and how
to call them.

Each schema follows the OpenAI function calling format:
https://platform.openai.com/docs/guides/function-calling
"""

from typing import List, Dict

# ──────────────────────────────────────────────────────────────
# Import schemas from each tool module
# ──────────────────────────────────────────────────────────────

from tools.calculator import SCHEMA as CALCULATOR_SCHEMA
from tools.web_search import SCHEMA as WEB_SEARCH_SCHEMA
from tools.slack import SCHEMA as SLACK_SCHEMA
from tools.weather import SCHEMA as WEATHER_SCHEMA
from tools.stock import SCHEMA as STOCK_SCHEMA
from tools.database import SCHEMA as DATABASE_SCHEMA
from tools.file_reader import SCHEMA as FILE_READER_SCHEMA


# ──────────────────────────────────────────────────────────────
# OpenAI-style tool definitions
# Each tool is wrapped in the {type: "function", function: {...}} format
# ──────────────────────────────────────────────────────────────

def _wrap(schema: Dict) -> Dict:
    """Wrap a raw schema into OpenAI tool format."""
    return {
        "type": "function",
        "function": schema,
    }


# ── Core Tools (required for Day 13) ─────────────────────────

CORE_TOOLS: List[Dict] = [
    _wrap(CALCULATOR_SCHEMA),
    _wrap(WEB_SEARCH_SCHEMA),
    _wrap(SLACK_SCHEMA),
]

# ── All Tools (core + stretch) ───────────────────────────────

ALL_TOOLS: List[Dict] = [
    _wrap(CALCULATOR_SCHEMA),
    _wrap(WEB_SEARCH_SCHEMA),
    _wrap(SLACK_SCHEMA),
    _wrap(WEATHER_SCHEMA),
    _wrap(STOCK_SCHEMA),
    _wrap(DATABASE_SCHEMA),
    _wrap(FILE_READER_SCHEMA),
]

# ── Cohere-style tool definitions ────────────────────────────


def get_cohere_tools(include_stretch: bool = False) -> List[Dict]:
    """
    Get tools for Cohere's V2 API (same OpenAI format).
    Cohere V2 expects: {"type": "function", "function": {...}}
    """
    if include_stretch:
        return ALL_TOOLS
    return CORE_TOOLS


# ──────────────────────────────────────────────────────────────
# Display all schemas
# ──────────────────────────────────────────────────────────────


def print_schemas(tools: List[Dict]):
    """Pretty-print all tool schemas."""
    for t in tools:
        func = t.get("function", t)
        name = func.get("name", "?")
        desc = func.get("description", "?")
        params = func.get("parameters", {}).get("properties", {})
        required = func.get("parameters", {}).get("required", [])

        print(f"\n{'='*60}")
        print(f"📌 {name}")
        print(f"   {desc}")
        print(f"{'='*60}")

        if params:
            print("   Parameters:")
            for p_name, p_info in params.items():
                req = " REQUIRED" if p_name in required else ""
                e = ""
                if "enum" in p_info:
                    e = f" [{', '.join(p_info['enum'])}]"
                print(f"     • {p_name}: {p_info.get('type', 'string')}{req}{e}")
                if "description" in p_info:
                    print(f"       {p_info['description']}")
        else:
            print("   (no parameters)")


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("📋 Tool Schemas (OpenAI Format)")
    print("=" * 60)

    print("\n🔹 CORE TOOLS (calculator, search_web, send_slack):")
    print_schemas(CORE_TOOLS)

    print("\n\n🔹 STRETCH TOOLS (weather, stock, database, file_reader):")
    print_schemas(ALL_TOOLS[3:])

    print("\n\n🔹 Cohere Format Example:")
    import json
    cohere_tools = get_cohere_tools(include_stretch=False)
    print(json.dumps(cohere_tools, indent=2))

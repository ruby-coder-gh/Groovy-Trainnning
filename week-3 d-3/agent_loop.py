"""
🔄 Agent Loop — Tool Selection + Execution (Cohere)

Part 3 + Part 6 of Day 13 — The core loop that:
1. Takes a user query
2. LLM decides which tool to use
3. Executes the tool
4. Returns the result to the user

This version uses Cohere's Command R+ which has native tool/function calling.
"""

import os
import sys
import json
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv

from registry import REGISTRY, list_tools
from schemas import get_cohere_tools

# Load environment variables from .env
load_dotenv()

# ──────────────────────────────────────────────────────────────
# Cohere client setup
# ──────────────────────────────────────────────────────────────

try:
    import cohere
except ImportError:
    cohere = None  # type: ignore


def get_cohere_client():
    """Initialize and return the Cohere client."""
    if cohere is None:
        raise ImportError(
            "cohere package not installed.\n"
            "Run: pip install cohere>=5.0.0"
        )

    api_key = os.getenv("COHERE_API_KEY")
    if not api_key or api_key == "your-cohere-api-key-here":
        raise ValueError(
            "❌ COHERE_API_KEY not set in .env file.\n"
            "   Get a free key at: https://dashboard.cohere.com/api-keys"
        )

    return cohere.ClientV2(api_key)


# ──────────────────────────────────────────────────────────────
# Tool execution
# ──────────────────────────────────────────────────────────────


def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> str:
    """
    Look up a tool in the registry and execute it with the given parameters.

    Args:
        tool_name: Name of the tool to execute
        parameters: Dict of parameter names → values

    Returns:
        String result of tool execution (always a string, even for numeric results)
    """
    if tool_name not in REGISTRY:
        return f"❌ Unknown tool: '{tool_name}'. Valid: {', '.join(REGISTRY.keys())}"

    try:
        tool_fn = REGISTRY[tool_name]["function"]
        result = tool_fn(**parameters)

        # Normalize to string
        if isinstance(result, (int, float)):
            return str(result)
        return str(result)

    except TypeError as e:
        return f"❌ Invalid parameters for '{tool_name}': {e}"
    except ValueError as e:
        return f"❌ Error in '{tool_name}': {e}"
    except Exception as e:
        return f"❌ Unexpected error in '{tool_name}': {e}"


# ──────────────────────────────────────────────────────────────
# Agent Loop
# ──────────────────────────────────────────────────────────────


def agent_loop(
    user_query: str,
    max_turns: int = 5,
    verbose: bool = True,
    include_stretch: bool = False,
) -> str:
    """
    Run the agent loop: user query → LLM decides tool → execute → return.

    Args:
        user_query: The user's natural language request
        max_turns: Maximum number of tool calls before forcing an answer
        verbose: If True, print each step of the loop
        include_stretch: If True, include weather/stock/database/file tools

    Returns:
        The final answer from the LLM
    """
    client = get_cohere_client()
    model = os.getenv("COHERE_MODEL", "command-r-08-2024")

    # Get available tools from the schemas module
    tools = get_cohere_tools(include_stretch=include_stretch)

    # System prompt
    system_prompt = (
        "You are a helpful AI assistant with access to tools. "
        "You can perform calculations, search the web, send Slack messages, "
        "check the weather, look up stock prices, query databases, and read files. "
        "Always use the appropriate tool when needed. "
        "When you get a tool result, incorporate it into a natural, helpful response.\n\n"
        f"Available tools: {', '.join(REGISTRY.keys())}"
    )

    # Build messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    if verbose:
        print(f"\n{'='*60}")
        print(f"🤖 AGENT LOOP STARTING")
        print(f"{'='*60}")
        print(f"📝 User: {user_query}")
        print(f"🔧 Tools: {len(tools)} registered")
        print(f"{'='*60}\n")

    # ── Main conversation loop ────────────────────────────────
    for turn in range(max_turns):
        if verbose:
            print(f"\n─── Turn {turn + 1}/{max_turns} ──────────────────────")

        # ── Step 1: Call LLM ──────────────────────────────────
        try:
            response = client.chat(
                model=model,
                messages=messages,
                tools=tools,
            )
        except Exception as e:
            error_msg = f"❌ Cohere API error: {e}"
            if verbose:
                print(error_msg)
            return error_msg

        # ── Step 2: Check for tool calls ──────────────────────
        if response.message.tool_calls:
            tool_calls = response.message.tool_calls

            # Add assistant message with tool calls to history
            messages.append({
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
                "content": None,
            })

            # ── Step 3: Execute each tool ─────────────────────
            for tc in tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                except json.JSONDecodeError:
                    args = {}

                if verbose:
                    print(f"  🛠️  Calling tool: {name}")
                    print(f"     Args: {json.dumps(args, indent=4)}")

                result = execute_tool(name, args)

                if verbose:
                    # Show a preview of the result (first 200 chars)
                    preview = result[:200] + "…" if len(result) > 200 else result
                    print(f"     Result: {preview}")

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            # Continue the loop — LLM will see tool results
            continue

        # ── Step 4: No tool calls → LLM gave final answer ─────
        final_answer = response.message.content[0].text if response.message.content else "I don't have an answer."

        if verbose:
            print(f"\n  💬 Final answer: {final_answer}")

        return final_answer

    # If we exhaust max_turns, force a final response
    if verbose:
        print(f"\n⚠️  Max turns ({max_turns}) reached. Forcing final answer...")

    try:
        response = client.chat(
            model=model,
            messages=messages,
        )
        return response.message.content[0].text if response.message.content else "Max turns reached without a final answer."
    except Exception as e:
        return f"❌ Error getting final answer: {e}"


# ──────────────────────────────────────────────────────────────
# Interactive CLI mode
# ──────────────────────────────────────────────────────────────


def interactive_loop(include_stretch: bool = False):
    """Run the agent in interactive CLI mode."""
    print("\n" + "=" * 60)
    print("  🤖 AI AGENT — Tool Calling Mode (Cohere)")
    print("=" * 60)
    print("  Available tools:")
    print(list_tools())
    print()
    print("  Type 'exit' to quit, 'tools' to list available tools")
    print("-" * 60)

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("👋 Goodbye!")
            break
        if user_input.lower() in ("tools", "help"):
            print(list_tools())
            continue

        result = agent_loop(user_input, verbose=True, include_stretch=include_stretch)
        print(f"\n🤖 Agent: {result}")


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with a simple query
    print("Testing agent loop with a calculator query...")
    result = agent_loop("What is 45 * 12?", verbose=True, include_stretch=False)
    print(f"\n{'='*60}")
    print(f"Final result: {result}")

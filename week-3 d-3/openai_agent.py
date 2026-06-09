"""
🤖 OpenAI Agent Loop — Function Calling

Uses OpenAI's function calling API to power the agent loop
for Day 13 Tool Use project.
"""

import os
import sys
import json
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv

from registry import REGISTRY, list_tools
from agent_loop import execute_tool
from schemas import CORE_TOOLS, ALL_TOOLS

load_dotenv()

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = os.getenv("OPENAI_MODEL", "gpt-4o")

SYSTEM_PROMPT = (
    "You are a helpful AI assistant with access to tools. "
    "You can perform calculations, search the web, send Slack messages, "
    "check the weather, look up stock prices, query databases, and read files. "
    "Always use the appropriate tool when needed. "
    "When you get a tool result, incorporate it into a natural, helpful response.\n\n"
    f"Available tools: {', '.join(REGISTRY.keys())}"
)


def openai_agent_loop(
    user_query: str,
    max_turns: int = 5,
    verbose: bool = True,
    include_stretch: bool = False,
) -> str:
    """
    Run the agent loop using OpenAI function calling.

    Args:
        user_query: The user's natural language request
        max_turns: Maximum number of tool calls before forcing an answer
        verbose: If True, print each step of the loop
        include_stretch: If True, include weather/stock/database/file tools

    Returns:
        The final answer from the LLM
    """
    tools = ALL_TOOLS if include_stretch else CORE_TOOLS

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]

    if verbose:
        print(f"\n{'='*60}")
        print(f"🤖 OPENAI AGENT LOOP STARTING")
        print(f"{'='*60}")
        print(f"📝 User: {user_query}")
        print(f"🔧 Tools: {len(tools)} registered")
        print(f"{'='*60}\n")

    for turn in range(max_turns):
        if verbose:
            print(f"\n─── Turn {turn + 1}/{max_turns} ──────────────────────")

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
            )
        except Exception as e:
            error_msg = f"❌ OpenAI API error: {e}"
            if verbose:
                print(error_msg)
            return error_msg

        choice = response.choices[0]
        message = choice.message

        if message.tool_calls:
            tool_calls = message.tool_calls

            messages.append({
                "role": "assistant",
                "content": message.content or "",
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
            })

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
                    preview = result[:200] + "…" if len(result) > 200 else result
                    print(f"     Result: {preview}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            continue

        final_answer = message.content or "I don't have an answer."

        if verbose:
            print(f"\n  💬 Final answer: {final_answer}")

        return final_answer

    if verbose:
        print(f"\n⚠️  Max turns ({max_turns}) reached. Forcing final answer...")

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return response.choices[0].message.content or "Max turns reached without a final answer."
    except Exception as e:
        return f"❌ Error getting final answer: {e}"


def interactive_loop(include_stretch: bool = False):
    """Run the agent in interactive CLI mode."""
    print("\n" + "=" * 60)
    print("  🤖 AI AGENT — Function Calling Mode (OpenAI)")
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

        result = openai_agent_loop(
            user_input, verbose=True, include_stretch=include_stretch
        )
        print(f"\n🤖 Agent: {result}")


if __name__ == "__main__":
    print("Testing OpenAI agent loop with a calculator query...")
    result = openai_agent_loop(
        "What is 45 * 12?", verbose=True, include_stretch=False
    )
    print(f"\n{'='*60}")
    print(f"Final result: {result}")

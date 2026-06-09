#!/usr/bin/env python3
"""
🤖 AI Agent — Tool Use & Function Calling

CLI entry point for Day 13 project.
Choose between Cohere (default) or OpenAI backend.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

from registry import list_tools, REGISTRY


def show_welcome(backend: str, include_stretch: bool):
    """Display the welcome banner with tool list."""
    print("\n" + "=" * 60)
    print(f"  🤖 AI AGENT — {backend.title()} Backend")
    print("=" * 60)
    print(list_tools())
    print()
    print("  Commands:  exit/quit/q  — Quit")
    print("             tools        — List available tools")
    print("             help         — Show this help")
    print("-" * 60)


def single_query(query: str, backend: str, stretch: bool, model: str | None):
    """Run a single query in non-interactive mode."""
    if backend == "openai":
        from openai_agent import openai_agent_loop
        loop_fn = openai_agent_loop
    else:
        from agent_loop import agent_loop
        loop_fn = agent_loop

    result = loop_fn(query, verbose=False, include_stretch=stretch)
    print(result)


def main():
    parser = argparse.ArgumentParser(
        description="🤖 AI Agent — Tool Use & Function Calling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s                          Interactive mode (Cohere)\n"
            "  %(prog)s --openai                 Interactive mode (OpenAI)\n"
            "  %(prog)s --stretch                Include stretch tools\n"
            "  %(prog)s -o -q \"What is 2+2?\"     Single query (OpenAI)\n"
            "  %(prog)s --query \"Weather in NYC\"  Single query (Cohere)\n"
        ),
    )
    parser.add_argument(
        "--openai", "-o",
        action="store_true",
        help="Use OpenAI backend (default: Cohere)",
    )
    parser.add_argument(
        "--stretch", "-s",
        action="store_true",
        help="Include stretch tools (weather, stock, database, file_reader)",
    )
    parser.add_argument(
        "--query", "-q",
        type=str,
        default=None,
        metavar="QUERY",
        help="Single query mode — run one query and exit",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        metavar="MODEL",
        help="Override the default model name",
    )

    args = parser.parse_args()

    backend = "openai" if args.openai else "cohere"

    if args.model:
        key = "OPENAI_MODEL" if args.openai else "COHERE_MODEL"
        os.environ[key] = args.model

    if args.query:
        single_query(args.query, backend, args.stretch, args.model)
        return

    show_welcome(backend, args.stretch)

    if backend == "openai":
        from openai_agent import interactive_loop
    else:
        from agent_loop import interactive_loop

    interactive_loop(include_stretch=args.stretch)


if __name__ == "__main__":
    main()

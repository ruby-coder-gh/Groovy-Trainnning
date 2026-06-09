#!/usr/bin/env python3
"""
🤖 Day 14 — Multi-Step Agents: LangChain vs LlamaIndex vs Pure SDK

Main CLI entry point.
Choose which agent framework to use, or run the comparison.
"""

import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

# Add sub-agent directories to path so imports work
BASE = os.path.dirname(os.path.abspath(__file__))
for sub in ["1-langchain-agent", "2-llamaindex-agent", "3-pure-sdk-agent", "4-memory"]:
    p = os.path.join(BASE, sub)
    if p not in sys.path:
        sys.path.insert(0, p)


def show_welcome():
    """Display welcome banner."""
    print("\n" + "=" * 60)
    print("  🤖 DAY 14 — MULTI-STEP AGENTS")
    print("  LangChain vs LlamaIndex vs Pure SDK")
    print("=" * 60)
    print("""
  Available modes:
    1. langchain    — LangChain agent (ZERO_SHOT_REACT_DESCRIPTION)
    2. llamaindex   — LlamaIndex RAG agent
    3. pure-sdk     — Pure OpenAI SDK agent (no framework)
    4. compare      — Run same query through ALL 3 and compare
    5. memory       — Test short-term + long-term memory

  Shorthand: lc, li, ps, cmp, mem
    """)


def main():
    parser = argparse.ArgumentParser(
        description="Day 14 — Multi-Step Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="langchain",
        choices=["langchain", "lc", "llamaindex", "li", "pure-sdk", "ps", "compare", "cmp", "memory", "mem"],
        help="Which agent to run (default: langchain)",
    )
    parser.add_argument("-q", "--query", type=str, help="Single query mode")

    args = parser.parse_args()

    mode = args.mode
    if mode in ("lc",):
        mode = "langchain"
    elif mode in ("li",):
        mode = "llamaindex"
    elif mode in ("ps",):
        mode = "pure-sdk"
    elif mode in ("cmp",):
        mode = "compare"
    elif mode in ("mem",):
        mode = "memory"

    if mode == "memory":
        run_memory_demo()
        return

    if mode == "compare":
        run_compare(args.query)
        return

    # Run specific agent
    run_agent(mode, args.query)


def run_agent(mode: str, query: str = None):
    """Run a specific agent framework."""
    dir_map = {
        "langchain": "1-langchain-agent",
        "llamaindex": "2-llamaindex-agent",
        "pure-sdk": "3-pure-sdk-agent",
    }

    ag_dir = dir_map.get(mode)
    if not ag_dir:
        print(f"❌ Unknown mode: {mode}")
        return

    ag_path = os.path.join(BASE, ag_dir, "agent.py")
    if not os.path.exists(ag_path):
        print(f"❌ Agent file not found: {ag_path}")
        return

    # Run the agent's own CLI (handles -q and interactive)
    import runpy
    # Pass query via args
    old_argv = sys.argv.copy()
    if query:
        sys.argv = ["agent.py", "-q", query]
    else:
        sys.argv = ["agent.py"]
    try:
        runpy.run_path(ag_path, run_name="__main__")
    finally:
        sys.argv = old_argv


def run_compare(query: str = None):
    """Run comparison across all 3 frameworks."""
    from compare import run_comparison
    if query:
        run_comparison([("Custom", query)])
    else:
        run_comparison()


def run_memory_demo():
    """Run memory demonstrations."""
    print("\n" + "=" * 60)
    print("  🧠 MEMORY SYSTEM")
    print("  Short-Term + Long-Term Memory Demo")
    print("=" * 60)

    # Add memory path
    mem_path = os.path.join(os.path.dirname(__file__), "4-memory")
    if mem_path not in sys.path:
        sys.path.insert(0, mem_path)

    # Short-term memory demo
    print("\n─── Short-Term Memory ───────────────────")
    from short_term import ShortTermMemory
    stm = ShortTermMemory(window_size=4)
    stm.add_system("You are a helpful assistant.")
    stm.add_user("What is AI?")
    stm.add_assistant("Artificial Intelligence is the simulation of human intelligence.")
    stm.add_user("Tell me more.")
    stm.add_assistant("AI includes ML, deep learning, NLP, and computer vision.")
    print(f"  Memory: {stm}")
    print(f"  Context size: {len(stm.get_context())} messages")
    for m in stm.get_context():
        print(f"    [{m['role']}] {m['content'][:60]}...")

    # Long-term memory demo
    print("\n─── Long-Term Memory ────────────────────")
    from long_term import LongTermMemory
    ltm = LongTermMemory()
    ltm.clear_all()
    ltm.remember("name", "Nikunj")
    ltm.remember("goal", "Become an AI Engineer")
    ltm.remember("favorite_topic", "Agentic Systems")
    ltm.remember("day", "Day 14 — Multi-Step Agents")
    print(f"  Total facts stored: {ltm.count()}")
    print(f"  Recall 'goal': {ltm.recall('goal')}")
    print(f"  Search 'AI': {len(ltm.search('AI'))} matches")
    print(f"\n  LLM Context Injection:")
    print(ltm.format_context())
    ltm.clear_all()


if __name__ == "__main__":
    show_welcome()
    main()

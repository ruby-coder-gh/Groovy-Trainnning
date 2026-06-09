#!/usr/bin/env python3
"""
🚀 Daily Standup Agent — Entry Point
======================================
Collect team standup updates, let Gemini generate a team status,
save to SQLite, and post to Slack.

Usage
-----
    export GEMINI_API_KEY="your-key-here"
    export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."

    # Interactive mode (enter updates one by one)
    python run_standup_agent.py

    # Demo mode (uses built-in sample updates)
    python run_standup_agent.py --demo

    # Load from JSON file
    python run_standup_agent.py --file updates.json
"""
from __future__ import annotations

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))

# Auto-load .env if it exists
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            val = val.strip("\"'")
            if not os.environ.get(key):
                os.environ[key] = val

from src.agent import Agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_standup")

# ── Sample standup updates for demo mode ───────────────────────────

DEMO_UPDATES = [
    {
        "author": "Alice",
        "yesterday": "Completed JWT auth refactor. Deployed to staging.",
        "today": "Start rate-limiting middleware",
        "blockers": "None",
    },
    {
        "author": "Bob",
        "yesterday": "Dashboard redesign PR is up for review",
        "today": "Work on notification center component",
        "blockers": "Waiting on Charlie for API specs",
    },
    {
        "author": "Charlie",
        "yesterday": "Working on notification API endpoints",
        "today": "First draft of notification API",
        "blockers": "Need Alice to review endpoint design",
    },
    {
        "author": "Diana",
        "yesterday": "Tested login flow, found 3 edge cases",
        "today": "Write E2E tests for dashboard",
        "blockers": "None",
    },
]

JSON_EXAMPLE = """Example JSON file:
[
  {
    "author": "Alice",
    "yesterday": "Fixed login bug",
    "today": "Add tests",
    "blockers": "None"
  }
]
"""


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Daily Standup Agent — Groovy AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--file", "-f", help="Path to JSON file with updates")
    parser.add_argument("--date", "-d", help="Standup date (ISO, default: today)")
    parser.add_argument("--no-slack", action="store_true",
                        help="Skip Slack notification")
    parser.add_argument("--demo", action="store_true",
                        help="Run with built-in demo updates")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show agent trace in real-time")

    args = parser.parse_args()

    # ── Resolve updates ────────────────────────────────────────
    updates = []
    if args.demo:
        updates = DEMO_UPDATES
        print(f"\n📢 Using {len(updates)} demo standup updates\n")
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        raw = json.loads(path.read_text(encoding="utf-8"))
        updates = raw if isinstance(raw, list) else [raw]
        print(f"\n📢 Loaded {len(updates)} updates from {args.file}\n")
    else:
        # Interactive mode
        print("📝 Enter team standup updates (type 'done' when finished):\n")
        while True:
            author = input("  Name (or 'done'): ").strip()
            if author.lower() == "done":
                break
            yesterday = input("  Yesterday: ").strip()
            today = input("  Today: ").strip()
            blockers = input("  Blockers: ").strip()
            updates.append({
                "author": author,
                "yesterday": yesterday,
                "today": today,
                "blockers": blockers or "None",
            })
            print()

        if not updates:
            print("❌ No updates provided.")
            sys.exit(1)

    # ── Check API key ──────────────────────────────────────────
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set.")
        print("   Get a free key: https://aistudio.google.com/apikey")
        print("   Then: export GEMINI_API_KEY='your-key'")
        sys.exit(1)

    # ── Run the agent ──────────────────────────────────────────
    agent = Agent()
    if args.verbose:
        agent.set_verbose(True)

    print("🤖 Agent: Processing standup updates...\n")
    result = agent.run_standup(
        updates=updates,
        standup_date=args.date,
        send_slack=not args.no_slack,
    )

    # ── Output ─────────────────────────────────────────────────
    if "error" in result:
        print(f"❌ Agent failed: {result['error']}")
        sys.exit(1)

    print("\n" + "━" * 50)
    print("☀️  TEAM STANDUP REPORT")
    print("━" * 50)
    print(result["team_status"])

    print("\n" + "━" * 50)
    print("📥 ENTRIES SAVED")
    print("━" * 50)
    for entry in result["entries_saved"]:
        print(f"  ✓ {entry['author']} (id={entry['id']})")

    print(f"\n💾 Saved to SQLite")

    slack_configured = bool(os.getenv("SLACK_WEBHOOK_URL"))
    if not args.no_slack:
        if slack_configured:
            print("📤 Sent to Slack ✓")
        else:
            print("📤 Slack webhook not configured (set SLACK_WEBHOOK_URL)")

    if args.verbose:
        agent.print_trace()

    print("\n✅ Done.\n")


if __name__ == "__main__":
    main()

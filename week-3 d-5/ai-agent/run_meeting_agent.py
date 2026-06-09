#!/usr/bin/env python3
"""
🚀 Meeting Summary Agent — Entry Point
=======================================
Summarise a meeting transcript, extract action items, save to SQLite,
and notify the team on Slack.

Usage
-----
    export GEMINI_API_KEY="your-key-here"
    export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."

    # Interactive mode (paste your transcript)
    python run_meeting_agent.py

    # File mode
    python run_meeting_agent.py --file transcript.txt --title "Sprint Planning"

    # Demo mode (uses a built-in sample transcript)
    python run_meeting_agent.py --demo
"""
from __future__ import annotations

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path so we can import src
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
logger = logging.getLogger("run_meeting")

# ── Sample transcript for demo mode ────────────────────────────────

DEMO_TRANSCRIPT = """
Alice (Engineering Lead):
We completed the user authentication refactor yesterday. The JWT token
rotation is now working in staging. Today I'll start on the rate-limiting
middleware. No blockers.

Bob (Frontend):
Finished the dashboard redesign. PR is up for review. Today I'll pick up
the notification center component. Blocked on Charlie for the API specs.

Charlie (Backend):
Still working on the notification API. Should have the first draft done
by EOD. I need Alice to review the endpoint design before we merge.

Diana (QA):
Tested the login flow — found 3 edge cases with special characters in
passwords. Logged them as bugs. Today I'll write E2E tests for the
dashboard.
"""


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Meeting Summary Agent — Groovy AI Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--file", "-f", help="Path to transcript file")
    parser.add_argument("--title", "-t", default="Team Sync",
                        help="Meeting title (default: 'Team Sync')")
    parser.add_argument("--date", "-d", help="Meeting date (ISO format, default: today)")
    parser.add_argument("--no-slack", action="store_true",
                        help="Skip Slack notification")
    parser.add_argument("--demo", action="store_true",
                        help="Run with a built-in demo transcript")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show agent trace in real-time")

    args = parser.parse_args()

    # ── Resolve transcript ─────────────────────────────────────
    if args.demo:
        title = "Sprint Team Sync — Week 12"
        transcript = DEMO_TRANSCRIPT
        print(f"\n📄 Using demo transcript: \"{title}\"\n")
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        transcript = path.read_text(encoding="utf-8")
        title = args.title
        print(f"\n📄 Loaded transcript from {args.file}\n")
    else:
        # Interactive — read from stdin
        print("📝 Paste your meeting transcript (Ctrl+D / Ctrl+Z when done):\n")
        transcript = sys.stdin.read().strip()
        if not transcript:
            print("❌ No transcript provided.")
            sys.exit(1)
        title = args.title

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

    print("🤖 Agent: Processing meeting transcript...\n")
    result = agent.run_meeting_summary(
        title=title,
        transcript=transcript,
        meeting_date=args.date,
        send_slack=not args.no_slack,
    )

    # ── Output ─────────────────────────────────────────────────
    if "error" in result:
        print(f"❌ Agent failed: {result['error']}")
        sys.exit(1)

    print("\n" + "━" * 50)
    print("📋 MEETING SUMMARY")
    print("━" * 50)
    print(result["summary"])

    print("\n" + "━" * 50)
    print("🔑 KEY TOPICS")
    print("━" * 50)
    print(result["key_topics"])

    print("\n" + "━" * 50)
    print("✅ ACTION ITEMS")
    print("━" * 50)
    for i, item in enumerate(result["action_items"], 1):
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            item.get("priority", "").lower(), "⚪"
        )
        print(f"  {i}. {priority_icon} {item.get('owner', '?')} → "
              f"{item.get('description', '')} "
              f"[{item.get('priority', 'med')}]")

    print(f"\n💾 Saved to SQLite (meeting #{result['meeting_id']})")

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

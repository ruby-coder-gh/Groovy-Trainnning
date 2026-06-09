#!/usr/bin/env python3
"""
🎯 Groovy AI Agent — Everything Demo
======================================
Runs BOTH the Meeting Summary Agent and Daily Standup Agent
back-to-back with sample data.

This is the "wow the leadership" demo that shows the full architecture:
  Input → Think → Act (Gemini) → Observe → Memorise (SQLite) → Notify (Slack)

Usage
-----
    export GEMINI_API_KEY="your-key-here"
    export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."   # optional

    python examples/demo_all_in_one.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Auto-load .env if it exists
_env_path = Path(__file__).parent.parent / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            val = val.strip("\"'")
            if not os.environ.get(key):
                os.environ[key] = val

from src.agent import Agent


# ── Demo Data ──────────────────────────────────────────────────────

MEETING_TRANSCRIPT = """
Alice (Engineering Lead):
We completed the user authentication refactor yesterday. The JWT token
rotation is now working in staging. Today I'll start on the rate-limiting
middleware. We need to decide on the rate limit thresholds.

Bob (Frontend):
Finished the dashboard redesign — it's now responsive and matches the
new design system. PR is up for review (#142). Today I'll pick up the
notification center component. I'm blocked on Charlie for the API specs.

Charlie (Backend):
Still working on the notification API. Got the WebSocket connections
working. Should have the first draft of the REST endpoints done by EOD.
I need Alice to review the endpoint design before we merge.

Diana (QA):
Tested the login flow with the new JWT changes — found 3 edge cases with
special characters in passwords. Logged them as bugs. I'll write E2E
tests for the dashboard redesign today.
"""

STANDUP_UPDATES = [
    {
        "author": "Alice",
        "yesterday": "Reviewed Charlie's notification API design. Merged auth refactor PR.",
        "today": "Start implementing rate-limiting middleware. Design review at 2 PM.",
        "blockers": "Waiting for Bob's dashboard PR to be ready for QA.",
    },
    {
        "author": "Bob",
        "yesterday": "Notification center component — wireframe approved. Started on the dropdown UI.",
        "today": "Finish notification center UI. Write unit tests.",
        "blockers": "Charlie said the WebSocket events will be ready by tomorrow, not today.",
    },
    {
        "author": "Charlie",
        "yesterday": "WebSocket event emitter working in staging. REST endpoints 90% done.",
        "today": "Finish notification REST endpoints. Write integration tests.",
        "blockers": "None. Just need reviews from Alice.",
    },
    {
        "author": "Diana",
        "yesterday": "Finished E2E tests for dashboard. Found 2 minor a11y issues, filed them.",
        "today": "Test notification center once Charlie's endpoints are deployed to staging.",
        "blockers": "Blocked until Charlie deploys to staging.",
    },
]


# ── Pretty Printer ─────────────────────────────────────────────────

def print_section(title: str, content: str, icon: str = "📋") -> None:
    width = 60
    print(f"\n{'═' * width}")
    print(f"  {icon}  {title}")
    print(f"{'═' * width}")
    print(f"\n{content}\n")


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   🎯  Groovy AI Agent — Full Demo          ║")
    print("║   Meeting Summary + Daily Standup          ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    agent = Agent()

    # ── 1. Meeting Summary ──────────────────────────────────
    print("▀" * 60)
    print("  PHASE 1: MEETING SUMMARY AGENT")
    print("▄" * 60)

    result = agent.run_meeting_summary(
        title="Sprint Team Sync — Week 12",
        transcript=MEETING_TRANSCRIPT,
        send_slack=True,
    )

    if "error" in result:
        print(f"\n❌ Meeting agent failed: {result['error']}")
        return

    print_section("Summary", result["summary"], "📝")
    print_section("Key Topics", result["key_topics"], "🔑")
    print_section("Action Items",
                  "\n".join(
                      f"  {i}. {item['owner']} → {item['description']} "
                      f"[{item['priority']}]"
                      for i, item in enumerate(result["action_items"], 1)
                  ),
                  "✅")
    print(f"  💾 Saved as meeting #{result['meeting_id']}")

    # ── 2. Daily Standup ────────────────────────────────────
    print("\n" + "▀" * 60)
    print("  PHASE 2: DAILY STANDUP AGENT")
    print("▄" * 60)

    result2 = agent.run_standup(
        updates=STANDUP_UPDATES,
        send_slack=True,
    )

    if "error" in result2:
        print(f"\n❌ Standup agent failed: {result2['error']}")
        return

    print_section("Team Standup Report", result2["team_status"], "☀️")
    print("  👤 Entries saved:")
    for e in result2["entries_saved"]:
        print(f"     ✓ {e['author']} (id={e['id']})")

    # ── 3. Show the trace ───────────────────────────────────
    print("\n" + "▀" * 60)
    print("  AGENT TRACE (think → act → observe → result)")
    print("▄" * 60)
    print()
    for step in agent.get_trace():
        icons = {"think": "🤔", "act": "🛠️", "observe": "👀", "result": "✅"}
        icon = icons.get(step["type"], "•")
        print(f"  {icon} [{step['type'].upper()}] {step['detail']}")

    print(f"\n{'═' * 60}")
    print("  ✅  Full demo complete!  ")
    print(f"{'═' * 60}")
    print()
    print("  Agent architecture used:")
    print("    • Pure Python agent loop (think → act → observe → result)")
    print("    • Gemini Free API for LLM reasoning")
    print("    • SQLite for persistent memory")
    print("    • Slack webhook for team notifications")
    print("    • GitHub API for code context (available but not used in this demo)")
    print()


if __name__ == "__main__":
    main()

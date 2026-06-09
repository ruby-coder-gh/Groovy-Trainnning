"""
📢 Slack Webhook Tool

Sends messages to Slack via incoming webhook.

Part 5 of Day 13 — Lets the agent notify teams, post updates, and trigger alerts.
"""

import os
import sys
import json
from typing import Optional

import requests


def send_slack(
    message: str,
    webhook_url: Optional[str] = None,
) -> str:
    """
    Send a message to Slack via webhook.

    Args:
        message: The message text to send
        webhook_url: Slack webhook URL (defaults to SLACK_WEBHOOK_URL env var)

    Returns:
        Success/error message string
    """
    url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")

    if not url:
        # Fallback: print to console instead of Slack
        print("\n[📢 SLACK FALLBACK (no webhook configured)]")
        print(f"  Message: {message}")
        print("[End Slack fallback]\n")
        return f"✅ Slack message printed to console (no webhook URL configured): {message}"

    try:
        payload = {"text": message}
        resp = requests.post(
            url,
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return f"✅ Slack message sent successfully: {message}"
    except requests.exceptions.Timeout:
        return "❌ Slack webhook timed out after 10 seconds"
    except requests.exceptions.RequestException as e:
        return f"❌ Slack error: {e}"
    except Exception as e:
        return f"❌ Unexpected error sending Slack message: {e}"


# ──────────────────────────────────────────────────────────────
# JSON Schema for tool calling
# ──────────────────────────────────────────────────────────────

SCHEMA = {
    "name": "send_slack",
    "description": "Send a notification message to a Slack channel via webhook. Use this to alert teams, report status, or share results.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The message text to send to Slack",
            },
        },
        "required": ["message"],
    },
}


# ──────────────────────────────────────────────────────────────
# Smoke test
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("📢 Slack Tool Test")
    print("-" * 40)
    result = send_slack("🤖 AI Agent completed task successfully!")
    print(result)

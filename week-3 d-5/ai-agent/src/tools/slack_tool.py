"""
Slack Tool — post messages to a Slack channel via webhook.

No Slack API scopes, no OAuth — just a simple HTTPS POST to an
incoming webhook URL.  Free for any workspace.
"""
from __future__ import annotations

import os
import json
import logging
import urllib.request
import urllib.error

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)


class SlackTool(Tool):
    """
    Send rich-text messages to a Slack channel.

    Environment
    -----------
    SLACK_WEBHOOK_URL : str
        The full https://hooks.slack.com/... URL from your Slack workspace.
    """

    name: str = "slack"
    description: str = (
        "Post a message to the team's Slack channel. "
        "Use this to notify the team about meeting summaries, "
        "standup reports, or important action items."
    )

    def __init__(self, webhook_url: str | None = None) -> None:
        super().__init__()
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL", "")

    # ── execute ────────────────────────────────────────────────────

    def execute(
        self,
        *,
        message: str = "",
        title: str = "🤖 Agent Notification",
        color: str = "#36a64f",      # Slack's green
        fields: list[dict] | None = None,
    ) -> ToolResult:
        """
        Post a richly formatted message to Slack.

        Parameters
        ----------
        message : str
            The main text (supports Slack mrkdwn).
        title : str
            Bold title at the top of the attachment.
        color : str
            Hex colour for the sidebar stripe.
        fields : list[dict], optional
            Slack attachment fields, e.g.::

                [{"title": "Status", "value": "✅ Complete", "short": True}]

        Returns
        -------
        ToolResult
        """
        if not self.webhook_url:
            return ToolResult(
                success=False,
                error="SLACK_WEBHOOK_URL is not set. "
                      "Create one at https://api.slack.com/messaging/webhooks",
            )

        payload = self._build_payload(message, title, color, fields or [])
        return self._post(payload)

    # ── internal ───────────────────────────────────────────────────

    def _build_payload(
        self,
        message: str,
        title: str,
        color: str,
        fields: list[dict],
    ) -> dict:
        return {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": fields,
                    "footer": "Groovy AI Agent",
                    "ts": int(__import__("time").time()),
                }
            ]
        }

    def _post(self, payload: dict) -> ToolResult:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8")
                if body == "ok":
                    logger.info("Slack message sent successfully")
                    return ToolResult(success=True, data={"response": "ok"})
                return ToolResult(success=True, data={"response": body})
        except urllib.error.HTTPError as exc:
            logger.exception("Slack webhook HTTP error")
            return ToolResult(
                success=False,
                error=f"Slack HTTP {exc.code}: {exc.read().decode()}",
            )
        except Exception as exc:
            logger.exception("Slack webhook failed")
            return ToolResult(success=False, error=str(exc))

    # ── quick helpers ──────────────────────────────────────────────

    def send_summary(self, summary_text: str, meeting_title: str) -> ToolResult:
        """Post a meeting summary to Slack."""
        return self.execute(
            message=summary_text,
            title=f"📝 Summary: {meeting_title}",
            color="#36a64f",
        )

    def send_standup(self, team_status: str) -> ToolResult:
        """Post the daily standup report to Slack."""
        return self.execute(
            message=team_status,
            title="☀️ Daily Standup Report",
            color="#4A90D9",
        )

    def send_error(self, context: str, error: str) -> ToolResult:
        """Post an error notification to Slack (red attachment)."""
        return self.execute(
            message=f"*Error during:* {context}\n```{error}```",
            title="🚨 Agent Error",
            color="#DC143C",
        )

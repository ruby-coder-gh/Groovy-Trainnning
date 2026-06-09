"""
Pure-Python Agent Loop — the brain of the operation.

Architecture
────────────
The agent follows a simple, transparent loop:

  1. RECEIVE input (transcript, standup updates, etc.)
  2. THINK — decide which tool to use and why
  3. ACT — invoke the chosen tool
  4. OBSERVE — capture the tool's result
  5. REPEAT if needed, or produce final output
  6. MEMORISE — persist to SQLite
  7. NOTIFY — post to Slack

No LangGraph. No CrewAI. No MCP.
Just clean Python that you can read, trace, and debug in one sitting.
"""
from __future__ import annotations

import json
import logging
import textwrap
from datetime import date
from typing import Any, Callable

from .tools import (
    Tool,
    ToolResult,
    GeminiTool,
    SQLiteTool,
    SlackTool,
    GitHubTool,
)
from .prompts.templates import (
    MEETING_SUMMARY_SYSTEM,
    MEETING_SUMMARY_USER,
    STANDUP_SYSTEM,
    STANDUP_USER,
)

logger = logging.getLogger(__name__)


# ── Step tracking ──────────────────────────────────────────────────

class Step:
    """A single step in the agent's trace — think / act / observe."""

    def __init__(self, step_type: str, detail: str) -> None:
        self.type = step_type       # think | act | observe | result
        self.detail = detail

    def __repr__(self) -> str:
        return f"[{self.type.upper()}] {self.detail[:120]}"


# ── Agent ──────────────────────────────────────────────────────────

class Agent:
    """
    A lightweight, tool-using agent that can summarise meetings,
    process daily standups, and notify teams via Slack.

    Usage
    -----
    >>> agent = Agent()
    >>> result = agent.run_meeting_summary(
    ...     title="Sprint Planning",
    ...     transcript="...",
    ... )
    >>> print(result["summary"])
    """

    def __init__(
        self,
        gemini_api_key: str | None = None,
        slack_webhook_url: str | None = None,
        db_path: str = "data/agent_memory.db",
    ) -> None:
        # ── register tools ─────────────────────────────────────
        self.tools: dict[str, Tool] = {
            "gemini": GeminiTool(api_key=gemini_api_key),
            "sqlite": SQLiteTool(db_path=db_path),
            "slack": SlackTool(webhook_url=slack_webhook_url),
            "github": GitHubTool(),
        }
        self._steps: list[Step] = []
        self._verbose: bool = False

    # ── properties ─────────────────────────────────────────────────

    @property
    def llm(self) -> GeminiTool:
        return self.tools["gemini"]  # type: ignore[return-value]

    @property
    def memory(self) -> SQLiteTool:
        return self.tools["sqlite"]  # type: ignore[return-value]

    @property
    def notifier(self) -> SlackTool:
        return self.tools["slack"]  # type: ignore[return-value]

    # ── tracing ────────────────────────────────────────────────────

    def _trace(self, step_type: str, detail: str) -> None:
        step = Step(step_type, detail)
        self._steps.append(step)
        if self._verbose:
            print(f"  {step}")

    def get_trace(self) -> list[dict]:
        """Return the full trace as a list of dicts (for display)."""
        return [{"type": s.type, "detail": s.detail} for s in self._steps]

    def print_trace(self) -> None:
        """Pretty-print the agent's decision trace."""
        print("\n━━━ Agent Trace ━━━")
        for s in self._steps:
            icon = {"think": "🤔", "act": "🛠️", "observe": "👀", "result": "✅"}.get(s.type, "•")
            print(f"  {icon} [{s.type.upper()}] {s.detail}")
        print("━━━━━━━━━━━━━━━━\n")

    # ── Meeting Summary Agent ──────────────────────────────────────

    def run_meeting_summary(
        self,
        title: str,
        transcript: str,
        meeting_date: str | None = None,
        send_slack: bool = True,
    ) -> dict[str, Any]:
        """
        Full meeting-summary pipeline:

        1. THINK — decide what to extract
        2. ACT — call Gemini with summary prompt
        3. OBSERVE — parse the LLM response
        4. MEMORISE — save meeting + action items to SQLite
        5. NOTIFY — post summary to Slack (optional)

        Parameters
        ----------
        title : str
            Meeting title (e.g. "Sprint Retro — Week 12").
        transcript : str
            Raw meeting transcript / notes.
        meeting_date : str, optional
            ISO date (defaults to today).
        send_slack : bool
            Whether to post to Slack.

        Returns
        -------
        dict with keys: summary, key_topics, action_items, meeting_id, trace
        """
        self._steps.clear()
        mdate = meeting_date or date.today().isoformat()

        # ── 1. THINK ───────────────────────────────────────────
        self._trace("think", f"Received meeting \"{title}\" ({mdate}), transcript length={len(transcript)} chars")  # noqa: E501
        self._trace("think", "Planning: ask Gemini to summarise + extract action items")

        # ── 2. ACT: Gemini ─────────────────────────────────────
        self._trace("act", f"Calling Gemini (model={self.llm.model}) with meeting prompt")
        system = MEETING_SUMMARY_SYSTEM
        prompt = MEETING_SUMMARY_USER.format(title=title, date=mdate, transcript=transcript)
        llm_result = self.llm(system=system, prompt=prompt, max_output_tokens=4096)

        if not llm_result:
            self._trace("observe", f"Gemini failed: {llm_result.error}")
            return {"error": llm_result.error, "trace": self.get_trace()}

        # ── 3. OBSERVE ─────────────────────────────────────────
        raw_text = llm_result.data["text"]
        self._trace("observe", f"Gemini responded ({len(raw_text)} chars)")
        parsed = self._parse_meeting_output(raw_text)

        # ── 4. MEMORISE ────────────────────────────────────────
        self._trace("act", "Saving meeting record to SQLite")
        meeting_id = self.memory.save_meeting(
            title=title,
            transcript_snippet=transcript[:500],
            summary=parsed["summary"],
            key_topics=parsed["key_topics"],
            meeting_date=mdate,
        )
        self._trace("observe", f"Saved meeting #{meeting_id}")

        for item in parsed["action_items"]:
            self._trace("act", f"Saving action item: {item['description'][:60]}...")
            self.memory.execute(
                action="save_action_item",
                meeting_id=meeting_id,
                owner=item["owner"],
                description=item["description"],
                priority=item["priority"],
                deadline=item.get("deadline", ""),
            )

        # ── 5. NOTIFY ──────────────────────────────────────────
        if send_slack:
            self._trace("act", "Posting summary to Slack")
            slack_text = self._format_summary_for_slack(
                title, mdate, parsed, meeting_id,
            )
            slack_result = self.notifier.send_summary(slack_text, title)
            self._trace("observe",
                        f"Slack {'sent' if slack_result.success else 'failed'}")

        self._trace("result", "Meeting summary complete ✓")
        return {
            "summary": parsed["summary"],
            "key_topics": parsed["key_topics"],
            "action_items": parsed["action_items"],
            "meeting_id": meeting_id,
            "trace": self.get_trace(),
        }

    # ── Daily Standup Agent ────────────────────────────────────────

    def run_standup(
        self,
        updates: list[dict[str, str]],
        standup_date: str | None = None,
        send_slack: bool = True,
    ) -> dict[str, Any]:
        """
        Daily standup pipeline:

        1. THINK — process N team-member updates
        2. ACT — Gemini combines into a team status
        3. OBSERVE — parse the response
        4. MEMORISE — save individual + summary to SQLite
        5. NOTIFY — post to Slack

        Parameters
        ----------
        updates : list[dict]
            Each dict: ``{"author": "...", "yesterday": "...",
            "today": "...", "blockers": "..."}``
        standup_date : str, optional
            ISO date (defaults to today).
        send_slack : bool
            Whether to post to Slack.

        Returns
        -------
        dict with keys: team_status, entries_saved, trace
        """
        self._steps.clear()
        sdate = standup_date or date.today().isoformat()

        # ── 1. THINK ───────────────────────────────────────────
        self._trace("think", f"Processing {len(updates)} standup updates for {sdate}")

        # Format updates for the prompt
        formatted = []
        for u in updates:
            formatted.append(
                f"**{u['author']}**\n"
                f"  Yesterday: {u.get('yesterday', '—')}\n"
                f"  Today: {u.get('today', '—')}\n"
                f"  Blockers: {u.get('blockers', 'None')}\n"
            )
        updates_text = "\n".join(formatted)

        # ── 2. ACT: Gemini ─────────────────────────────────────
        self._trace("act", "Calling Gemini to generate team status")
        system = STANDUP_SYSTEM
        prompt = STANDUP_USER.format(updates=updates_text, date=sdate)
        llm_result = self.llm(system=system, prompt=prompt, max_output_tokens=4096)

        if not llm_result:
            self._trace("observe", f"Gemini failed: {llm_result.error}")
            return {"error": llm_result.error, "trace": self.get_trace()}

        team_status = llm_result.data["text"]
        self._trace("observe", f"Gemini generated team status ({len(team_status)} chars)")

        # ── 3. MEMORISE ────────────────────────────────────────
        entries_saved = []
        for u in updates:
            self._trace("act", f"Saving standup for {u['author']}")
            eid = self.memory.save_standup(
                author=u["author"],
                yesterday=u.get("yesterday", ""),
                today=u.get("today", ""),
                blockers=u.get("blockers", ""),
                team_summary=team_status,
                standup_date=sdate,
            )
            entries_saved.append({"author": u["author"], "id": eid})

        # ── 4. NOTIFY ──────────────────────────────────────────
        if send_slack:
            self._trace("act", "Posting standup report to Slack")
            slack_result = self.notifier.send_standup(team_status)
            self._trace("observe",
                        f"Slack {'sent' if slack_result.success else 'failed'}")

        self._trace("result", "Daily standup complete ✓")
        return {
            "team_status": team_status,
            "entries_saved": entries_saved,
            "trace": self.get_trace(),
        }

    # ── Generic agent loop (extensible) ────────────────────────────

    def run(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[str] | None = None,
        max_steps: int = 5,
    ) -> dict[str, Any]:
        """
        Generic think-act-observe loop.

        This is the extensible version. You can pass any system prompt
        and user message, and the agent will use its tools to respond.

        For now this is a simple ReAct-style loop. In future it can be
        extended with tool selection, multi-turn reasoning, etc.
        """
        self._steps.clear()
        self._trace("think", "Starting generic agent loop")
        self._trace("act", "Calling Gemini with system + user prompt")

        result = self.llm(system=system_prompt, prompt=user_message)
        if not result.success:
            return {"error": result.error, "trace": self.get_trace()}

        self._trace("observe", f"Response received ({len(result.data['text'])} chars)")
        self._trace("result", "Generic agent loop complete ✓")
        return {
            "response": result.data["text"],
            "trace": self.get_trace(),
        }

    # ── Helpers ────────────────────────────────────────────────────

    def _parse_meeting_output(self, text: str) -> dict[str, Any]:
        """
        Naive-but-effective parser for the LLM's structured markdown.

        Extracts:
        - Summary (text after "## Summary")
        - Key Topics (bullet points after "## Key Topics")
        - Action Items (table rows after "## Action Items")
        """
        result: dict[str, Any] = {
            "summary": "",
            "key_topics": "",
            "action_items": [],
        }

        # Extract sections by header
        sections = text.split("## ")

        for section in sections:
            section = section.strip()
            if section.startswith("Summary"):
                result["summary"] = section.replace("Summary", "", 1).strip()
            elif section.startswith("Key Topics"):
                result["key_topics"] = section.replace("Key Topics", "", 1).strip()
            elif section.startswith("Action Items"):
                items_text = section.replace("Action Items", "", 1).strip()
                result["action_items"] = self._parse_action_items(items_text)

        return result

    def _parse_action_items(self, text: str) -> list[dict[str, str]]:
        """
        Parse action items from markdown table or bullet list.
        Handles both::

            | Owner | Description | Priority | Deadline |
            |-------|-------------|----------|----------|
            | Alice | Fix login   | High     | 2025-12-01 |

        And::

            - Owner: Alice, Task: Fix login, Priority: High
        """
        items: list[dict[str, str]] = []

        # Try table format first (lines with |)
        lines = [l.strip() for l in text.split("\n") if l.strip() and "|" in l]
        if lines:
            # Skip header separator line (---|---)
            data_lines = [l for l in lines if not all(c in "| -:" for c in l)][1:]
            for line in data_lines:
                cols = [c.strip() for c in line.split("|") if c.strip()]
                if len(cols) >= 2:
                    items.append({
                        "owner": cols[0] if len(cols) > 0 else "",
                        "description": cols[1] if len(cols) > 1 else "",
                        "priority": cols[2] if len(cols) > 2 else "medium",
                        "deadline": cols[3] if len(cols) > 3 else "",
                    })

        # If no table found, try bullet format
        if not items:
            for line in text.split("\n"):
                line = line.strip().lstrip("-* ")
                if ":" in line and not line.startswith(" ") and not line.startswith("|"):
                    parts = line.split(",")
                    item: dict[str, str] = {
                        "owner": "", "description": "", "priority": "medium", "deadline": ""
                    }
                    for part in parts:
                        part = part.strip()
                        if ":" in part:
                            key, val = part.split(":", 1)
                            k = key.strip().lower()
                            v = val.strip()
                            if "owner" in k:
                                item["owner"] = v
                            elif "desc" in k or "task" in k:
                                item["description"] = v
                            elif "prior" in k:
                                item["priority"] = v
                            elif "dead" in k or "due" in k:
                                item["deadline"] = v
                    if item["description"]:
                        items.append(item)

        return items if items else [{"owner": "—", "description": "No action items found", "priority": "—", "deadline": "—"}]  # noqa: E501

    def _format_summary_for_slack(
        self,
        title: str,
        date: str,
        parsed: dict,
        meeting_id: int,
    ) -> str:
        """Build a Slack-friendly mrkdwn message from parsed data."""
        lines = [
            f"*Meeting:* {title}",
            f"*Date:* {date}",
            f"*ID:* #{meeting_id}",
            "",
            "*📋 Summary*",
            parsed.get("summary", "N/A"),
            "",
            "*🔑 Key Topics*",
            parsed.get("key_topics", "N/A"),
            "",
            "*✅ Action Items*",
        ]
        for item in parsed.get("action_items", []):
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                item.get("priority", "").lower(), "⚪"
            )
            lines.append(
                f"  {priority_icon} *{item.get('owner', '?')}* → "
                f"{item.get('description', '')} "
                f"({item.get('deadline', 'no deadline')})"
            )
        return "\n".join(lines)

    def set_verbose(self, verbose: bool = True) -> None:
        self._verbose = verbose

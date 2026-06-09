"""
SQLite Tool — gives the agent read/write access to its memory store.

Every meeting summary, action item, and standup entry lives in a single
portable ``.db`` file.  No server, no config, no fuss.
"""
from __future__ import annotations

import sqlite3
import logging
from pathlib import Path
from typing import Any

from ..models.schema import (
    init_db,
    MeetingStore,
    StandupStore,
    MeetingRecord,
    ActionItem,
    StandupEntry,
)
from .base import Tool, ToolResult

logger = logging.getLogger(__name__)


class SQLiteTool(Tool):
    """
    Persistent key-value / table storage backed by SQLite.

    The agent can store meeting summaries, action items, standup entries,
    and retrieve recent history for context.
    """

    name: str = "sqlite"
    description: str = (
        "Store and retrieve data from a local SQLite database. "
        "Use this to save meeting summaries, action items, standup entries, "
        "and to fetch history."
    )

    def __init__(self, db_path: str | Path = "data/agent_memory.db") -> None:
        super().__init__()
        self._db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None
        self._meeting_store: MeetingStore | None = None
        self._standup_store: StandupStore | None = None

    # ── lazy connection ────────────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = init_db(self._db_path)
        return self._conn

    @property
    def meetings(self) -> MeetingStore:
        if self._meeting_store is None:
            self._meeting_store = MeetingStore(self.conn)
        return self._meeting_store

    @property
    def standups(self) -> StandupStore:
        if self._standup_store is None:
            self._standup_store = StandupStore(self.conn)
        return self._standup_store

    # ── execute ────────────────────────────────────────────────────

    def execute(  # type: ignore[override]
        self,
        *,
        action: str = "list_recent_meetings",
        **kwargs: Any,
    ) -> ToolResult:
        """
        Dispatch to the right storage operation.

        ``action`` can be one of:

        **Meeting actions**
        - ``save_meeting``        — store a MeetingRecord
        - ``get_meeting``         — fetch by id
        - ``list_recent_meetings``— last N meetings

        **Action-item actions**
        - ``save_action_item``    — store an ActionItem
        - ``list_action_items``   — items for a meeting_id

        **Standup actions**
        - ``save_standup``        — store a StandupEntry
        - ``list_recent_standups``— last N standup entries
        - ``list_standups_by_date``— entries for a given date
        """
        try:
            return self._dispatch(action, **kwargs)
        except Exception as exc:
            logger.exception("SQLiteTool action=%s failed", action)
            return ToolResult(success=False, error=str(exc))

    def _dispatch(self, action: str, **kw: Any) -> ToolResult:
        # ── meetings ────────────────────────────────────────────
        if action == "save_meeting":
            rec = MeetingRecord(
                title=kw.get("title", ""),
                transcript_snippet=kw.get("transcript_snippet", ""),
                summary=kw.get("summary", ""),
                key_topics=kw.get("key_topics", ""),
                meeting_date=kw.get("meeting_date", ""),
            )
            row_id = self.meetings.insert_meeting(rec)
            return ToolResult(success=True, data={"id": row_id})

        if action == "get_meeting":
            meeting = self.meetings.get_meeting(kw["meeting_id"])
            return ToolResult(success=True, data=meeting)

        if action == "list_recent_meetings":
            limit = kw.get("limit", 10)
            rows = self.meetings.get_recent_meetings(limit)
            return ToolResult(success=True, data={"meetings": rows})

        # ── action items ────────────────────────────────────────
        if action == "save_action_item":
            item = ActionItem(
                meeting_id=kw.get("meeting_id", 0),
                owner=kw.get("owner", ""),
                description=kw.get("description", ""),
                priority=kw.get("priority", "medium"),
                deadline=kw.get("deadline", ""),
                status=kw.get("status", "open"),
            )
            row_id = self.meetings.insert_action_item(item)
            return ToolResult(success=True, data={"id": row_id})

        if action == "list_action_items":
            items = self.meetings.get_action_items(kw["meeting_id"])
            return ToolResult(success=True, data={"action_items": items})

        # ── standups ────────────────────────────────────────────
        if action == "save_standup":
            entry = StandupEntry(
                author=kw.get("author", ""),
                yesterday=kw.get("yesterday", ""),
                today=kw.get("today", ""),
                blockers=kw.get("blockers", ""),
                team_summary=kw.get("team_summary", ""),
                standup_date=kw.get("standup_date", ""),
            )
            row_id = self.standups.insert_standup(entry)
            return ToolResult(success=True, data={"id": row_id})

        if action == "list_recent_standups":
            limit = kw.get("limit", 20)
            rows = self.standups.get_recent_standups(limit)
            return ToolResult(success=True, data={"standups": rows})

        if action == "list_standups_by_date":
            rows = self.standups.get_standups_by_date(kw["date"])
            return ToolResult(success=True, data={"standups": rows})

        # ── fallback ────────────────────────────────────────────
        return ToolResult(
            success=False,
            error=f"Unknown action '{action}'. "
                  f"Available: save_meeting, get_meeting, list_recent_meetings, "
                  f"save_action_item, list_action_items, "
                  f"save_standup, list_recent_standups, list_standups_by_date",
        )

    # ── convenience shortcuts for the agent ────────────────────────

    def save_meeting(self, **kw) -> int:
        return self.execute(action="save_meeting", **kw).data["id"]

    def save_standup(self, **kw) -> int:
        return self.execute(action="save_standup", **kw).data["id"]

    def recent_history(self, days: int = 7) -> str:
        """Return a human-readable snippet of recent activity."""
        meetings = self.execute(action="list_recent_meetings", limit=5)
        standups = self.execute(action="list_recent_standups", limit=10)
        parts = []
        if meetings.success and meetings.data.get("meetings"):
            parts.append("📋 Recent Meetings:")
            for m in meetings.data["meetings"]:
                parts.append(f"  • {m['title']} ({m['meeting_date']})")
        if standups.success and standups.data.get("standups"):
            parts.append("📢 Recent Standups:")
            for s in standups.data["standups"]:
                parts.append(f"  • {s['author']} on {s['standup_date']}")
        return "\n".join(parts) or "No history yet."

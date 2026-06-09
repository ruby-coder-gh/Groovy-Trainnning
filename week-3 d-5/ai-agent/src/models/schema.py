"""
SQLite schema & data-access helpers.
Keeps the agent's memory lightweight and portable — no ORM, no magic.
"""
from __future__ import annotations

import sqlite3
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Dataclasses ────────────────────────────────────────────────────

@dataclass
class MeetingRecord:
    """A single meeting that was summarised by the agent."""
    id: int | None = None
    title: str = ""
    transcript_snippet: str = ""
    summary: str = ""
    key_topics: str = ""
    meeting_date: str = ""
    created_at: str = ""


@dataclass
class ActionItem:
    """An action item extracted from a meeting."""
    id: int | None = None
    meeting_id: int = 0
    owner: str = ""
    description: str = ""
    priority: str = "medium"          # high / medium / low
    deadline: str = ""
    status: str = "open"              # open / in_progress / done
    created_at: str = ""


@dataclass
class StandupEntry:
    """A single daily-standup submission from a team member."""
    id: int | None = None
    author: str = ""
    yesterday: str = ""
    today: str = ""
    blockers: str = ""
    team_summary: str = ""
    standup_date: str = ""
    created_at: str = ""


# ── Schema DDL ─────────────────────────────────────────────────────

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meetings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL DEFAULT '',
    transcript_snippet TEXT NOT NULL DEFAULT '',
    summary         TEXT NOT NULL DEFAULT '',
    key_topics      TEXT NOT NULL DEFAULT '',
    meeting_date    TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS action_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id      INTEGER NOT NULL REFERENCES meetings(id),
    owner           TEXT NOT NULL DEFAULT '',
    description     TEXT NOT NULL DEFAULT '',
    priority        TEXT NOT NULL DEFAULT 'medium',
    deadline        TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL DEFAULT 'open',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS standup_entries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    author          TEXT NOT NULL DEFAULT '',
    yesterday       TEXT NOT NULL DEFAULT '',
    today           TEXT NOT NULL DEFAULT '',
    blockers        TEXT NOT NULL DEFAULT '',
    team_summary    TEXT NOT NULL DEFAULT '',
    standup_date    TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(meeting_date);
CREATE INDEX IF NOT EXISTS idx_action_items_meeting ON action_items(meeting_id);
CREATE INDEX IF NOT EXISTS idx_standups_date ON standup_entries(standup_date);
"""


# ── Initialisation ─────────────────────────────────────────────────

def init_db(db_path: str | Path) -> sqlite3.Connection:
    """Create / open the SQLite database and ensure tables exist."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    logger.info("Database ready at %s", db_path)
    return conn


# ── Data-access helpers ────────────────────────────────────────────

class MeetingStore:
    """Thin data-access layer for meetings + action_items."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # ── meetings ───────────────────────────────────────────────────

    def insert_meeting(self, rec: MeetingRecord) -> int:
        cur = self.conn.execute(
            """INSERT INTO meetings (title, transcript_snippet, summary,
               key_topics, meeting_date)
               VALUES (?, ?, ?, ?, ?)""",
            (rec.title, rec.transcript_snippet, rec.summary,
             rec.key_topics, rec.meeting_date),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_recent_meetings(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM meetings ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_meeting(self, meeting_id: int) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── action_items ───────────────────────────────────────────────

    def insert_action_item(self, item: ActionItem) -> int:
        cur = self.conn.execute(
            """INSERT INTO action_items (meeting_id, owner, description,
               priority, deadline, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (item.meeting_id, item.owner, item.description,
             item.priority, item.deadline, item.status),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_action_items(self, meeting_id: int) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM action_items WHERE meeting_id = ?",
            (meeting_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class StandupStore:
    """Thin data-access layer for standup entries."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert_standup(self, entry: StandupEntry) -> int:
        cur = self.conn.execute(
            """INSERT INTO standup_entries (author, yesterday, today,
               blockers, team_summary, standup_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (entry.author, entry.yesterday, entry.today,
             entry.blockers, entry.team_summary, entry.standup_date),
        )
        self.conn.commit()
        return cur.lastrowid  # type: ignore[return-value]

    def get_recent_standups(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM standup_entries ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_standups_by_date(self, date: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM standup_entries WHERE standup_date = ?",
            (date,),
        ).fetchall()
        return [dict(r) for r in rows]

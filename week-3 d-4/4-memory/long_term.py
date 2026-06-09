"""
🗄️ Long-Term Memory — Persistent Knowledge Storage

Part 6 of Day 14 — Stores user facts, preferences, and learned info
across sessions using SQLite.

This is how assistants become personalized.
"""

import os
import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


# Store DB next to this file
DB_PATH = Path(__file__).parent / "long_term_memory.db"


class LongTermMemory:
    """
    Persistent key-value memory store backed by SQLite.

    Stores facts like:
      - user_name: Nikunj
      - goal: Become AI Engineer
      - favorite_stack: Python

    Retrieval: search by keyword or get all relevant facts.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(DB_PATH)
        self._init_db()

    def _init_db(self) -> None:
        """Create the memory table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)
            """)
            conn.commit()

    def remember(self, key: str, value: str, category: str = "general") -> str:
        """
        Store a fact in long-term memory.

        Args:
            key: Unique identifier (e.g., "user_name", "goal")
            value: The fact value
            category: Grouping category (e.g., "personal", "preference", "fact")

        Returns:
            Confirmation message
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO memories (key, value, category, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    category = excluded.category,
                    updated_at = CURRENT_TIMESTAMP
            """, (key, value, category))
            conn.commit()
        return f"✅ Remembered: {key} = {value}"

    def recall(self, key: str) -> Optional[str]:
        """
        Recall a specific fact by key.

        Args:
            key: The fact key to retrieve

        Returns:
            The value if found, None otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM memories WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Search memories by keyword (searches keys and values).

        Args:
            query: Keyword to search for

        Returns:
            List of matching memory entries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """SELECT key, value, category, created_at, updated_at
                   FROM memories
                   WHERE key LIKE ? OR value LIKE ? OR category LIKE ?
                   ORDER BY updated_at DESC""",
                (f"%{query}%", f"%{query}%", f"%{query}%")
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_all(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all memories, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of all memory entries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if category:
                cursor = conn.execute(
                    "SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC",
                    (category,)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM memories ORDER BY category, updated_at DESC"
                )
            return [dict(row) for row in cursor.fetchall()]

    def forget(self, key: str) -> str:
        """
        Delete a specific memory.

        Args:
            key: The key to forget

        Returns:
            Confirmation message
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE key = ?", (key,))
            conn.commit()
            if cursor.rowcount > 0:
                return f"🗑️ Forgotten: {key}"
            return f"❌ No memory found with key: {key}"

    def clear_all(self) -> str:
        """Delete ALL memories. Use with caution."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memories")
            conn.commit()
        return "🗑️ All memories cleared."

    def format_context(self, query: Optional[str] = None) -> str:
        """
        Format memories as context for an LLM prompt.

        If query is provided, searches for relevant memories.
        Otherwise returns all memories.

        Returns:
            Formatted string to inject into system prompt
        """
        if query:
            items = self.search(query)
        else:
            items = self.get_all()

        if not items:
            return ""

        lines = ["\n📌 Known facts about the user:"]
        for item in items:
            lines.append(f"  - {item['key']}: {item['value']}")
        return "\n".join(lines)

    def count(self) -> int:
        """Count total memories stored."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
            return row[0] if row else 0

    def to_dict(self) -> Dict[str, str]:
        """Export all memories as a flat dictionary."""
        result = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key, value FROM memories")
            for row in cursor:
                result[row[0]] = row[1]
        return result


# ──────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("🗄️  Long-Term Memory Demo")
    print("-" * 40)

    mem = LongTermMemory()

    # Clear for clean demo
    mem.clear_all()

    # Store some facts
    mem.remember("name", "Nikunj")
    mem.remember("goal", "Become an AI Engineer")
    mem.remember("favorite_stack", "Python + AI")
    mem.remember("learning", "Multi-Step Agents (Day 14)")
    mem.remember("email", "nikunj@example.com", category="contact")

    print(f"\n📊 Total memories: {mem.count()}")

    print("\n--- Recall specific ---")
    print(f"  name: {mem.recall('name')}")
    print(f"  goal: {mem.recall('goal')}")

    print("\n--- Search 'AI' ---")
    for r in mem.search("AI"):
        print(f"  {r['key']}: {r['value']}")

    print("\n--- All by category ---")
    for r in mem.get_all():
        print(f"  [{r['category']}] {r['key']}: {r['value']}")

    print("\n--- Formatted for LLM ---")
    print(mem.format_context())

    # Cleanup
    mem.clear_all()
    print(f"\n🧹 Cleaned up. Count: {mem.count()}")

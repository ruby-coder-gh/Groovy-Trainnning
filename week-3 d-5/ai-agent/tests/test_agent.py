"""
Tests for the Groovy AI Agent.

These tests focus on the agent's core logic and tool integration.
The Gemini and Slack tools are mocked to avoid real API calls.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.tools.base import ToolResult
from src.tools.sqlite_tool import SQLiteTool
from src.tools.slack_tool import SlackTool
from src.tools.github_tool import GitHubTool
from src.models.schema import (
    init_db,
    MeetingRecord,
    ActionItem,
    StandupEntry,
    MeetingStore,
    StandupStore,
)
from src.prompts.templates import (
    MEETING_SUMMARY_SYSTEM,
    MEETING_SUMMARY_USER,
    STANDUP_SYSTEM,
    STANDUP_USER,
    build_agent_prompt,
)
from src.agent import Agent


# ═══════════════════════════════════════════════════════════════════
#  SQLite Tool Tests
# ═══════════════════════════════════════════════════════════════════

class TestSQLiteTool:
    @pytest.fixture
    def db_path(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            yield f.name
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def tool(self, db_path):
        return SQLiteTool(db_path=db_path)

    def test_init_creates_tables(self, db_path):
        """Calling init_db should create tables."""
        conn = init_db(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = [r["name"] for r in tables]
        assert "meetings" in names
        assert "action_items" in names
        assert "standup_entries" in names

    def test_save_and_get_meeting(self, tool):
        """Saving a meeting and retrieving it should work."""
        tool.execute(
            action="save_meeting",
            title="Sprint Planning",
            transcript_snippet="We discussed...",
            summary="Planned sprint 12",
            key_topics="Auth, Dashboard",
            meeting_date="2026-06-09",
        )
        result = tool.execute(action="list_recent_meetings", limit=5)
        assert result.success
        assert len(result.data["meetings"]) == 1
        assert result.data["meetings"][0]["title"] == "Sprint Planning"

    def test_save_and_get_action_items(self, tool):
        """Saving action items and retrieving by meeting_id."""
        mid = tool.save_meeting(
            title="Retro",
            transcript_snippet="...",
            summary="Good sprint",
            key_topics="Process",
            meeting_date="2026-06-09",
        )
        tool.execute(
            action="save_action_item",
            meeting_id=mid,
            owner="Alice",
            description="Fix login bug",
            priority="high",
        )
        result = tool.execute(action="list_action_items", meeting_id=mid)
        assert result.success
        assert len(result.data["action_items"]) == 1
        assert result.data["action_items"][0]["owner"] == "Alice"

    def test_save_and_get_standup(self, tool):
        """Saving a standup entry and retrieving by date."""
        tool.execute(
            action="save_standup",
            author="Bob",
            yesterday="Fixed bug",
            today="Writing tests",
            blockers="None",
            team_summary="Team is on track",
            standup_date="2026-06-09",
        )
        result = tool.execute(action="list_recent_standups", limit=5)
        assert result.success
        assert len(result.data["standups"]) == 1

        by_date = tool.execute(action="list_standups_by_date", date="2026-06-09")
        assert by_date.success
        assert len(by_date.data["standups"]) == 1

    def test_unknown_action(self, tool):
        """Unknown action should return error."""
        result = tool.execute(action="nonexistent")
        assert not result.success
        assert "Unknown" in result.error


# ═══════════════════════════════════════════════════════════════════
#  Slack Tool Tests
# ═══════════════════════════════════════════════════════════════════

class TestSlackTool:
    def test_no_webhook_returns_error(self):
        """Without a webhook URL, execute should return an error."""
        tool = SlackTool(webhook_url="")
        result = tool.execute(message="Test")
        assert not result.success
        assert "SLACK_WEBHOOK_URL" in result.error

    @patch("urllib.request.urlopen")
    def test_successful_post(self, mock_urlopen):
        """Happy path: Slack returns 'ok'."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        tool = SlackTool(webhook_url="https://hooks.slack.com/test")
        result = tool.execute(message="Hello from test!")
        assert result.success

    @patch("urllib.request.urlopen")
    def test_send_summary_helper(self, mock_urlopen):
        """send_summary should call execute with correct params."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        tool = SlackTool(webhook_url="https://hooks.slack.com/test")
        result = tool.send_summary("Summary text", "Team Sync")
        assert result.success

    @patch("urllib.request.urlopen")
    def test_send_standup_helper(self, mock_urlopen):
        """send_standup should post standup report."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"ok"
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        tool = SlackTool(webhook_url="https://hooks.slack.com/test")
        result = tool.send_standup("Team status...")
        assert result.success


# ═══════════════════════════════════════════════════════════════════
#  GitHub Tool Tests
# ═══════════════════════════════════════════════════════════════════

class TestGitHubTool:
    def test_no_repo_returns_error(self):
        """Missing repo should return error."""
        tool = GitHubTool()
        result = tool.execute(action="get_file", repo="", path="README.md")
        assert not result.success

    @patch("urllib.request.urlopen")
    def test_get_repo_info(self, mock_urlopen):
        """Fetching repo info should parse the response."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "name": "test-repo",
            "description": "A test repo",
            "language": "Python",
            "stargazers_count": 42,
            "forks_count": 7,
            "open_issues_count": 3,
            "default_branch": "main",
        }).encode()
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        tool = GitHubTool()
        result = tool.execute(action="get_repo_info", repo="owner/test-repo")
        assert result.success
        assert result.data["name"] == "test-repo"
        assert result.data["stars"] == 42


# ═══════════════════════════════════════════════════════════════════
#  Prompt Templates Tests
# ═══════════════════════════════════════════════════════════════════

class TestPromptTemplates:
    def test_meeting_summary_system_is_not_empty(self):
        assert len(MEETING_SUMMARY_SYSTEM) > 100

    def test_meeting_summary_user_formats_correctly(self):
        result = MEETING_SUMMARY_USER.format(
            title="Test", date="2026-06-09", transcript="Hello world"
        )
        assert "Test" in result
        assert "2026-06-09" in result
        assert "Hello world" in result

    def test_standup_system_is_not_empty(self):
        assert len(STANDUP_SYSTEM) > 100

    def test_standup_user_formats_correctly(self):
        result = STANDUP_USER.format(
            updates="- Alice: did X", date="2026-06-09"
        )
        assert "Alice" in result
        assert "2026-06-09" in result

    def test_build_agent_prompt_with_context(self):
        msgs = build_agent_prompt(
            system="You are a helper",
            user_message="Summarise this",
            context="Some context",
        )
        assert len(msgs) == 3
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "model"

    def test_build_agent_prompt_without_context(self):
        msgs = build_agent_prompt(
            system="You are a helper",
            user_message="Summarise this",
        )
        assert len(msgs) == 2


# ═══════════════════════════════════════════════════════════════════
#  Agent Tests (mocked Gemini)
# ═══════════════════════════════════════════════════════════════════

class TestAgent:
    @pytest.fixture
    def agent(self):
        """Create an agent with a mock Gemini tool."""
        a = Agent(
            gemini_api_key="fake-key",
            slack_webhook_url="https://hooks.slack.com/test",
            db_path=":memory:",
        )
        # Replace real tools with mocks
        a.tools["gemini"] = MagicMock()
        a.tools["gemini"].name = "gemini"
        a.tools["gemini"].model = "gemini-mock"
        a.tools["gemini"].return_value = ToolResult(
            success=True,
            data={"text": self._mock_summary_response()},
        )
        # Use in-memory SQLite
        real_sqlite = SQLiteTool(db_path=":memory:")
        a.tools["sqlite"] = real_sqlite
        return a

    def _mock_summary_response(self):
        return """## Summary
The team discussed sprint progress and blockers.

## Key Topics
- Authentication refactor
- Dashboard redesign
- Notification API

## Action Items
| Owner | Description | Priority | Deadline |
|-------|-------------|----------|----------|
| Alice | Fix login bug | High | 2026-06-15 |
| Bob | Complete dashboard | Medium | 2026-06-20 |
"""

    def test_run_meeting_summary(self, agent):
        """Meeting summary pipeline should produce expected output."""
        result = agent.run_meeting_summary(
            title="Sprint Sync",
            transcript="Alice: Done with auth...",
            send_slack=False,
        )
        assert "error" not in result
        assert "summary" in result
        assert "action_items" in result
        assert result["meeting_id"] > 0

    def test_run_meeting_summary_includes_trace(self, agent):
        """Trace should contain think/act/observe/result steps."""
        result = agent.run_meeting_summary(
            title="Test",
            transcript="Test transcript",
            send_slack=False,
        )
        assert "trace" in result
        trace = result["trace"]
        assert len(trace) > 0
        types = [t["type"] for t in trace]
        assert "think" in types
        assert "act" in types
        assert "observe" in types
        assert "result" in types

    def test_run_meeting_summary_gemini_failure(self, agent):
        """If Gemini fails, the agent should return an error."""
        agent.tools["gemini"].return_value = ToolResult(
            success=False, error="API error"
        )
        result = agent.run_meeting_summary(
            title="Test",
            transcript="Test",
            send_slack=False,
        )
        assert "error" in result

    def test_get_trace_returns_steps(self, agent):
        """get_trace should return all recorded steps."""
        agent._trace("think", "Thinking...")
        agent._trace("act", "Calling tool...")
        trace = agent.get_trace()
        assert len(trace) == 2
        assert trace[0]["type"] == "think"

    def test_parse_meeting_output(self, agent):
        """Internal parser should extract sections from LLM output."""
        text = self._mock_summary_response()
        parsed = agent._parse_meeting_output(text)
        assert parsed["summary"] != ""
        assert "authentication" in parsed["key_topics"].lower()
        assert len(parsed["action_items"]) >= 2

    def test_parse_action_items_table(self, agent):
        """Table-format action items should parse correctly."""
        table = """| Owner | Description | Priority | Deadline |
|-------|-------------|----------|----------|
| Alice | Fix login | High | 2026-06-15 |
| Bob | Tests | Low | 2026-06-20 |
"""
        items = agent._parse_action_items(table)
        assert len(items) >= 2
        assert items[0]["owner"] == "Alice"
        assert items[1]["priority"] == "Low"

    def test_format_summary_for_slack(self, agent):
        """Slack formatting should include key sections."""
        parsed = {
            "summary": "Good meeting",
            "key_topics": "- Auth\n- UI",
            "action_items": [{"owner": "Alice", "description": "Fix bug",
                              "priority": "high", "deadline": "2026-06-15"}],
        }
        formatted = agent._format_summary_for_slack(
            "Sprint", "2026-06-09", parsed, 1
        )
        assert "Good meeting" in formatted
        assert "Alice" in formatted
        assert "🔴" in formatted  # high priority indicator


# ═══════════════════════════════════════════════════════════════════
#  Standup Agent Tests
# ═══════════════════════════════════════════════════════════════════

class TestStandupAgent:
    @pytest.fixture
    def agent(self):
        a = Agent(
            gemini_api_key="fake-key",
            slack_webhook_url="",
            db_path=":memory:",
        )
        a.tools["gemini"] = MagicMock()
        a.tools["gemini"].name = "gemini"
        a.tools["gemini"].model = "gemini-mock"
        a.tools["gemini"].return_value = ToolResult(
            success=True,
            data={"text": "## Team Status\nEveryone is on track.\n\n### ✅ Completed\n- Auth done"},
        )
        a.tools["sqlite"] = SQLiteTool(db_path=":memory:")
        return a

    def test_run_standup(self, agent):
        """Standup pipeline should process updates and return team status."""
        updates = [
            {"author": "Alice", "yesterday": "Auth refactor",
             "today": "Rate limiting", "blockers": "None"},
            {"author": "Bob", "yesterday": "Dashboard",
             "today": "Notifications", "blockers": "API specs"},
        ]
        result = agent.run_standup(updates=updates, send_slack=False)
        assert "error" not in result
        assert "team_status" in result
        assert len(result["entries_saved"]) == 2
        assert result["entries_saved"][0]["author"] == "Alice"
        assert result["entries_saved"][1]["author"] == "Bob"

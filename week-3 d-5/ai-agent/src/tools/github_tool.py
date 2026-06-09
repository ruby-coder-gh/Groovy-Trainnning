"""
GitHub Tool — read public repository files via the GitHub REST API.

No tokens needed for public repos.  Useful when the agent needs to
reference code, config files, or documentation during a review.
"""
from __future__ import annotations

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Any

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubTool(Tool):
    """
    Fetch files and metadata from GitHub repositories.

    Environment
    -----------
    GITHUB_TOKEN : str, optional
        Personal access token (fine-grained) for *private* repos or
        higher rate limits.  Public repos work without a token.
    """

    name: str = "github"
    description: str = "Read files and metadata from GitHub repositories."

    def __init__(self, token: str | None = None) -> None:
        super().__init__()
        self._token = token or os.getenv("GITHUB_TOKEN", "")

    # ── public API ─────────────────────────────────────────────────

    def execute(  # type: ignore[override]
        self,
        *,
        action: str = "get_file",
        **kwargs: Any,
    ) -> ToolResult:
        """
        Dispatch to the right GitHub operation.

        ``action`` can be one of:
        - ``get_file``       — read a single file from a repo
        - ``list_repo_files``— list top-level files in a repo
        - ``get_repo_info``  — basic info about a repository
        """
        try:
            if action == "get_file":
                return self._get_file(**kwargs)
            if action == "list_repo_files":
                return self._list_files(**kwargs)
            if action == "get_repo_info":
                return self._repo_info(**kwargs)
            return ToolResult(
                success=False,
                error=f"Unknown GitHub action '{action}'",
            )
        except Exception as exc:
            logger.exception("GitHubTool action=%s failed", action)
            return ToolResult(success=False, error=str(exc))

    # ── get_file ───────────────────────────────────────────────────

    def _get_file(
        self,
        repo: str = "",
        path: str = "",
        branch: str = "main",
    ) -> ToolResult:
        """Fetch a single file's content (decoded from base64)."""
        if not repo or not path:
            return ToolResult(
                success=False,
                error="Both 'repo' (owner/name) and 'path' are required.",
            )

        url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}?ref={branch}"
        headers = self._headers()
        logger.info("Fetching %s/%s @ %s", repo, path, branch)

        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=headers), timeout=15
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return ToolResult(
                success=False,
                error=f"GitHub HTTP {exc.code}: {exc.reason}",
            )

        if isinstance(data, list):
            return ToolResult(
                success=True,
                data={
                    "type": "directory",
                    "entries": [item["name"] for item in data],
                },
            )

        import base64
        try:
            content = base64.b64decode(data["content"]).decode("utf-8")
        except Exception as exc:
            return ToolResult(success=False, error=f"Decode error: {exc}")

        return ToolResult(
            success=True,
            data={
                "type": "file",
                "name": data["name"],
                "path": data["path"],
                "size": data["size"],
                "content": content,
            },
        )

    # ── list_files ─────────────────────────────────────────────────

    def _list_files(
        self,
        repo: str = "",
        path: str = "",
        branch: str = "main",
    ) -> ToolResult:
        """List files in a directory within a repo."""
        return self._get_file(repo=repo, path=path, branch=branch)

    # ── repo_info ──────────────────────────────────────────────────

    def _repo_info(self, repo: str = "") -> ToolResult:
        if not repo:
            return ToolResult(success=False, error="'repo' (owner/name) is required.")
        url = f"{GITHUB_API_BASE}/repos/{repo}"
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=self._headers()), timeout=15
            ) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return ToolResult(
                success=True,
                data={
                    "name": data["name"],
                    "description": data.get("description", ""),
                    "language": data.get("language", ""),
                    "stars": data.get("stargazers_count", 0),
                    "forks": data.get("forks_count", 0),
                    "open_issues": data.get("open_issues_count", 0),
                    "default_branch": data.get("default_branch", "main"),
                },
            )
        except urllib.error.HTTPError as exc:
            return ToolResult(
                success=False,
                error=f"GitHub HTTP {exc.code}: {exc.reason}",
            )

    # ── headers ────────────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        h = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Groovy-AIAgent/1.0",
        }
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

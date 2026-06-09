"""
Abstract base for all agent tools.
Every tool wraps a single capability (LLM call, DB query, API request)
so the agent can → think → decide → act → observe → repeat.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    """Standardised envelope for every tool invocation."""
    success: bool
    data: Any = None
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return self.success


class Tool(ABC):
    """One tool = one capability the agent can reach for."""

    name: str = "unnamed_tool"
    description: str = ""

    def __init__(self) -> None:
        self._call_count: int = 0

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Run the tool with the given keyword arguments."""
        ...

    def __call__(self, **kwargs) -> ToolResult:
        self._call_count += 1
        logger.debug("Tool [%s] called (#%s) with kwargs=%s",
                      self.name, self._call_count, kwargs)
        try:
            result = self.execute(**kwargs)
            logger.debug("Tool [%s] → success=%s", self.name, result.success)
            return result
        except Exception as exc:
            logger.exception("Tool [%s] crashed", self.name)
            return ToolResult(success=False, error=str(exc))

    def reset_count(self) -> None:
        self._call_count = 0

    def tool_spec(self) -> dict:
        """Return a dict describing this tool for the agent's registry."""
        return {
            "name": self.name,
            "description": self.description,
        }

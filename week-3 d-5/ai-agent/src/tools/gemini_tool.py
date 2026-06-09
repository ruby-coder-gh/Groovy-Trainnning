"""
Gemini Tool — wraps the Google Gemini Free API.

Uses the `google-genai` SDK.  The free tier (Gemini 2.0 Flash / 1.5 Flash)
has generous rate limits and is perfect for prototyping and demos.
"""
from __future__ import annotations

import os
import time
import logging
from typing import Any

from google import genai
from google.genai import types as genai_types

from .base import Tool, ToolResult

logger = logging.getLogger(__name__)

# Default free-tier model — no cost, good quality
_DEFAULT_MODEL = "gemini-2.0-flash"
_MAX_RETRIES = 5               # how many times to retry on 429
_BASE_BACKOFF = 2.0            # seconds for first backoff


class GeminiTool(Tool):
    """
    Call Google Gemini with a system prompt + user message.

    Environment
    -----------
    GEMINI_API_KEY : str
        Your Google AI Studio API key (free).
    GEMINI_MODEL : str, optional
        Model name (default: gemini-2.0-flash).
    """

    name: str = "gemini"
    description: str = (
        "Send a prompt to Google Gemini and get back a text response. "
        "Use this for summarisation, extraction, and reasoning tasks."
    )

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_MODEL", _DEFAULT_MODEL)
        self._client: genai.Client | None = None

    # ── lazy client ────────────────────────────────────────────────

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            if not self.api_key:
                raise RuntimeError(
                    "GEMINI_API_KEY is not set. "
                    "Get a free key at https://aistudio.google.com/apikey"
                )
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    # ── execute ────────────────────────────────────────────────────

    def execute(
        self,
        *,
        system: str = "",
        prompt: str = "",
        context: str | None = None,
        temperature: float = 0.3,
        max_output_tokens: int = 4096,
        **kwargs: Any,
    ) -> ToolResult:
        """
        Send a prompt to Gemini and return the response.

        Parameters
        ----------
        system : str
            System-level instruction.
        prompt : str
            The user message / query.
        context : str, optional
            Extra context injected before the prompt.
        temperature : float
            Sampling temperature (default 0.3 for deterministic output).
        max_output_tokens : int
            Max tokens in the response.

        Returns
        -------
        ToolResult with ``data["text"]`` containing the model reply.
        """
        full_prompt = (
            f"{system}\n\n---\n\n{context}\n\n---\n\n{prompt}"
            if context
            else f"{system}\n\n---\n\n{prompt}"
        )

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                )
                text = response.text
                if attempt > 0:
                    logger.info("Gemini succeeded on retry #%s", attempt)
                return ToolResult(success=True, data={"text": text})
            except Exception as exc:
                last_error = exc
                err_str = str(exc)
                # Only retry on 429 (rate-limit / quota) or 5xx server errors
                if "429" in err_str or "500" in err_str or "503" in err_str:
                    backoff = _BASE_BACKOFF * (2 ** attempt)
                    logger.warning(
                        "Gemini API rate-limit (attempt %s/%s). "
                        "Backing off %.1fs …", attempt + 1, _MAX_RETRIES, backoff
                    )
                    time.sleep(backoff)
                else:
                    # Non-retriable error — bail immediately
                    logger.exception("Gemini API call failed (non-retriable)")
                    return ToolResult(
                        success=False,
                        error=f"Gemini error: {exc}",
                    )

        logger.exception("Gemini API call failed after %s retries", _MAX_RETRIES)
        return ToolResult(
            success=False,
            error=f"Gemini error after {_MAX_RETRIES} retries: {last_error}",
        )

    # ── structured output variant ──────────────────────────────────

    def generate_structured(
        self,
        *,
        system: str = "",
        prompt: str = "",
        response_model: type,
        context: str | None = None,
        temperature: float = 0.2,
    ) -> ToolResult:
        """
        Like ``execute()`` but parse the response into a Pydantic-like
        dataclass using Gemini's JSON mode.

        NOTE: The free-tier Gemini models support JSON mode via
        ``response_mime_type="application/json"``.
        """
        full_prompt = (
            f"{system}\n\n---\n\n{context}\n\n---\n\n{prompt}"
            if context
            else f"{system}\n\n---\n\n{prompt}"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=genai_types.GenerateContentConfig(
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=response_model,
                ),
            )
            return ToolResult(
                success=True,
                data={"parsed": response.parsed},
            )
        except Exception as exc:
            logger.exception("Gemini structured call failed")
            return ToolResult(
                success=False,
                error=f"Gemini structured error: {exc}",
            )

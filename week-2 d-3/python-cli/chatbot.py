#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────
# Day 8 / Week 2 Day 3 — Production-Grade CLI Chatbot v2 (Python)
# Streaming (asyncio + aiohttp) · Retry · Token Counting · Logging
#
# Usage:
#   python chatbot.py                              # default: ollama
#   python chatbot.py --provider openai
#   python chatbot.py --provider gemini
#   python chatbot.py --provider openai --model gpt-4o-mini
#   python chatbot.py --log-level debug
#
# Environment variables:
#   OPENAI_API_KEY         — required for OpenAI
#   GEMINI_API_KEY         — required for Gemini
#   CLI_LOG_LEVEL          — debug | info | warn | error
#   CLI_RETRY_MAX          — max retry attempts (default: 3)
#
# Install:  pip install aiohttp tiktoken
# ─────────────────────────────────────────────────────────────────────

import asyncio
import json
import os
import sys
import time
import argparse
import logging
import random
from pathlib import Path

# ─── Optional tiktoken for accurate token counting ─────────────
try:
    import tiktoken
    _TIKTOKEN_ENC = tiktoken.encoding_for_model("gpt-4o-mini")
except Exception:
    _TIKTOKEN_ENC = None

# ─── Optional aiohttp for async HTTP ───────────────────────────
try:
    import aiohttp
    import aiohttp.web
except ImportError:
    print("\033[31m[aiohttp] required. Install: pip install aiohttp\033[0m")
    sys.exit(1)


# ═════════════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ═════════════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="Production-Grade Multi-Provider CLI Chatbot v2"
    )
    parser.add_argument("--provider", default="ollama",
                        choices=["openai", "gemini", "ollama"],
                        help="Provider to use (default: ollama)")
    parser.add_argument("--model", default=None,
                        help="Override model name")
    parser.add_argument("--log-level", default=os.getenv("CLI_LOG_LEVEL", "info"),
                        choices=["debug", "info", "warn", "error", "silent"],
                        help="Logging level (default: info)")
    parser.add_argument("--retry-max", type=int,
                        default=int(os.getenv("CLI_RETRY_MAX", "3")),
                        help="Max retry attempts (default: 3)")
    parser.add_argument("--no-stream", action="store_true",
                        help="Disable streaming responses")
    parser.add_argument("--history", default=None,
                        help="Path to conversation history file (JSON)")
    return parser.parse_args()


CFG = parse_args()

# ═════════════════════════════════════════════════════════════════════
# 2. LOGGER
# ═════════════════════════════════════════════════════════════════════

LOG_LEVELS = {
    "silent": 0, "error": 1, "warn": 2, "info": 3, "debug": 4,
}
_log_level = LOG_LEVELS.get(CFG.log_level, 3)


def _log(level, msg, *args):
    if LOG_LEVELS.get(level, 0) <= _log_level:
        prefix = {
            "error": "\033[31m[ERROR]\033[0m",
            "warn": "\033[33m[WARN]\033[0m",
            "info": "\033[36m[INFO]\033[0m",
            "debug": "\033[90m[DEBUG]\033[0m",
        }.get(level, "")
        print(f"{prefix} {msg}", *args, file=sys.stderr if level == "error" else sys.stdout)


# ═════════════════════════════════════════════════════════════════════
# 3. RETRY — Exponential Backoff with Jitter
# ═════════════════════════════════════════════════════════════════════

def _backoff_delay(attempt: int, base_ms: float = 1000, max_ms: float = 60000) -> float:
    """Full jitter: delay = random(0, min(max, base * 2^attempt))"""
    exp = min(max_ms, base_ms * (2 ** attempt))
    return random.random() * exp / 1000  # return seconds


# ═════════════════════════════════════════════════════════════════════
# 4. TOKEN COUNTER
# ═════════════════════════════════════════════════════════════════════

def count_tokens(text: str) -> int:
    """Count tokens — uses tiktoken if available, otherwise approximate (~4 chars/token)."""
    if not text:
        return 0
    if _TIKTOKEN_ENC:
        return len(_TIKTOKEN_ENC.encode(text))
    return max(1, len(text) // 4)


def count_message_tokens(messages: list) -> int:
    """Count total tokens in a message list including overhead."""
    total = 0
    for m in messages:
        total += count_tokens(m.get("content") or "")
        total += 4  # role overhead
    total += 3  # base format
    return total


# ═════════════════════════════════════════════════════════════════════
# 5. PROVIDER DEFINITIONS
# ═════════════════════════════════════════════════════════════════════

def _build_openai_body(messages, model, stream):
    body = {"model": model, "messages": messages, "stream": stream}
    # Attach functions on first user message for demo
    if len(messages) <= 2:
        body["functions"] = [
            {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["city"],
                },
            }
        ]
        body["function_call"] = "auto"
    return body


def _build_gemini_body(messages, model, stream):
    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else m["role"]
        contents.append({
            "role": role,
            "parts": [{"text": m.get("content") or ""}]
        })
    return {"contents": contents}


def _build_ollama_body(messages, model, stream):
    return {"model": model, "messages": messages, "stream": stream}


PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o-mini",
        "url": "https://api.openai.com/v1/chat/completions",
        "cost_per_1m_in": 0.15,
        "cost_per_1m_out": 0.60,
        "build_body": _build_openai_body,
        "headers": lambda: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '')}",
        },
    },
    "gemini": {
        "name": "Gemini",
        "default_model": "gemini-2.0-flash",
        "url": lambda model: (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:streamGenerateContent?alt=sse&key={os.environ.get('GEMINI_API_KEY', '')}"
        ),
        "cost_per_1m_in": 0.075,
        "cost_per_1m_out": 0.30,
        "build_body": _build_gemini_body,
        "headers": lambda: {"Content-Type": "application/json"},
    },
    "ollama": {
        "name": "Ollama",
        "default_model": "qwen3:8b",
        "url": "http://localhost:11434/api/chat",
        "cost_per_1m_in": 0.0,
        "cost_per_1m_out": 0.0,
        "build_body": _build_ollama_body,
        "headers": lambda: {"Content-Type": "application/json"},
    },
}


def _get_provider_url(provider, model):
    url = provider["url"]
    if callable(url):
        return url(model)
    return url


# ═════════════════════════════════════════════════════════════════════
# 6. STREAMING PARSERS
# ═════════════════════════════════════════════════════════════════════

async def _parse_openai_stream(response):
    """Parse OpenAI SSE: data: {"choices":[{"delta":{"content":"..."}}]}"""
    async for line in response.content:
        decoded = line.decode("utf-8", errors="replace").strip()
        if not decoded or not decoded.startswith("data: "):
            continue
        payload = decoded[6:]
        if payload == "[DONE]":
            return
        try:
            chunk = json.loads(payload)
            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content")
            if content:
                yield content
        except json.JSONDecodeError:
            continue


async def _parse_gemini_stream(response):
    """Parse Gemini SSE: data: {"candidates":[{"content":{"parts":[{"text":"..."}]}}]}"""
    async for line in response.content:
        decoded = line.decode("utf-8", errors="replace").strip()
        if not decoded or not decoded.startswith("data: "):
            continue
        payload = decoded[6:]
        if not payload or payload == "[DONE]":
            continue
        try:
            chunk = json.loads(payload)
            parts = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            for part in parts:
                text = part.get("text", "")
                if text:
                    yield text
        except json.JSONDecodeError:
            continue


async def _parse_ollama_stream(response):
    """Parse Ollama NDJSON: {"message":{"content":"..."},"done":false}"""
    async for line in response.content:
        decoded = line.decode("utf-8", errors="replace").strip()
        if not decoded:
            continue
        try:
            chunk = json.loads(decoded)
            content = chunk.get("message", {}).get("content", "")
            if content:
                yield content
        except json.JSONDecodeError:
            continue


STREAM_PARSERS = {
    "openai": _parse_openai_stream,
    "gemini": _parse_gemini_stream,
    "ollama": _parse_ollama_stream,
}


# ═════════════════════════════════════════════════════════════════════
# 7. STREAMING API CALL WITH RETRY
# ═════════════════════════════════════════════════════════════════════

async def stream_response(session, provider, model, messages):
    """Stream response tokens from the provider with retry logic.
    
    Async generator that yields tokens as they arrive.
    """
    url = _get_provider_url(provider, model)
    body = provider["build_body"](messages, model, not CFG.no_stream)
    headers = provider["headers"]()

    for attempt in range(CFG.retry_max + 1):
        try:
            async with session.post(url, json=body, headers=headers,
                                    timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    _log("warn", f"API error {resp.status}: {err_text[:200]}")
                    if resp.status in (429, 500, 502, 503, 504) and attempt < CFG.retry_max:
                        delay = _backoff_delay(attempt)
                        _log("warn", f"Retry {attempt + 1}/{CFG.retry_max} in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                        continue
                    raise RuntimeError(f"{provider['name']} error {resp.status}: {err_text[:200]}")

                # Determine streaming format
                content_type = resp.headers.get("content-type", "")
                is_sse = "text/event-stream" in content_type

                if CFG.no_stream or not is_sse:
                    # Non-streaming fallback — yield the whole response
                    data = await resp.json()
                    text = ""
                    if provider["name"] == "OpenAI":
                        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    elif provider["name"] == "Gemini":
                        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                    elif provider["name"] == "Ollama":
                        text = data.get("message", {}).get("content", "")
                    if text:
                        yield text
                    return  # no value — just terminate generator

                # Streaming
                parser = STREAM_PARSERS.get(CFG.provider, _parse_openai_stream)
                async for token in parser(resp):
                    yield token
                return  # no value — just terminate generator

        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            _log("warn", f"Connection error: {e}")
            if attempt < CFG.retry_max:
                delay = _backoff_delay(attempt)
                _log("warn", f"Retry {attempt + 1}/{CFG.retry_max} in {delay:.1f}s...")
                await asyncio.sleep(delay)
                continue
            raise RuntimeError(f"Request failed after {CFG.retry_max} retries: {e}")

    raise RuntimeError("Max retries exceeded")


# ═════════════════════════════════════════════════════════════════════
# 8. FUNCTION CALLING (SIMULATED)
# ═════════════════════════════════════════════════════════════════════

def execute_function(fn_call: dict) -> dict:
    """Simulate function execution."""
    name = fn_call.get("name", "")
    args = json.loads(fn_call.get("arguments", "{}"))
    _log("info", f"Function called: {name}({json.dumps(args)})")

    if name == "get_weather":
        conditions = ["Sunny ☀️", "Cloudy ☁️", "Rainy 🌧️", "Windy 💨"]
        return {
            "city": args.get("city", "Unknown"),
            "temperature": 72 if args.get("unit") == "fahrenheit" else 22,
            "unit": args.get("unit", "celsius"),
            "condition": random.choice(conditions),
            "humidity": f"{random.randint(40, 80)}%",
        }
    return {"result": f"Function {name} executed (simulated)"}


# ═════════════════════════════════════════════════════════════════════
# 9. HISTORY PERSISTENCE
# ═════════════════════════════════════════════════════════════════════

def save_history(file_path: str, messages: list):
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(messages, indent=2), encoding="utf-8")
        _log("debug", f"History saved to {file_path}")
    except Exception as e:
        _log("warn", f"Could not save history: {e}")


def load_history(file_path: str) -> list:
    try:
        path = Path(file_path)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                _log("info", f"Loaded {len(data)} messages from history")
                return data
    except Exception as e:
        _log("warn", f"Could not load history: {e}")
    return []


# ═════════════════════════════════════════════════════════════════════
# 10. MAIN CHAT LOOP
# ═════════════════════════════════════════════════════════════════════

async def chat():
    # Validate provider
    provider = PROVIDERS.get(CFG.provider)
    if not provider:
        _log("error", f"Unknown provider: {CFG.provider}")
        sys.exit(1)

    model = CFG.model or provider["default_model"]

    if CFG.provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        _log("warn", "OPENAI_API_KEY not set")
    if CFG.provider == "gemini" and not os.environ.get("GEMINI_API_KEY"):
        _log("warn", "GEMINI_API_KEY not set")

    # Load history
    messages = []
    if CFG.history:
        messages = load_history(CFG.history)

    # Session tracking
    total_tokens_in = 0
    total_tokens_out = 0
    total_cost = 0.0
    total_latency = 0.0
    query_count = 0

    # ── Banner ────────────────────────────────────────────────
    print("")
    print("\033[32m╔════════════════════════════════════════════════════╗\033[0m")
    print("\033[32m║      🚀 Production CLI Bot v2 — Day 8            ║\033[0m")
    print("\033[32m║   Streaming · Retry · Token Counting             ║\033[0m")
    print("\033[32m╚════════════════════════════════════════════════════╝\033[0m")
    print(f"  \033[36mProvider:\033[0m  {provider['name']}")
    print(f"  \033[36mModel:\033[0m     {model}")
    print(f"  \033[36mStream:\033[0m    {'OFF' if CFG.no_stream else 'ON'}")
    print(f"  \033[36mRetries:\033[0m   {CFG.retry_max}")
    print(f"  \033[36mLog:\033[0m       {CFG.log_level}")
    cost_str = "Free (local)" if provider["cost_per_1m_in"] == 0 else \
        f"${provider['cost_per_1m_in']}/1M in · ${provider['cost_per_1m_out']}/1M out"
    print(f"  \033[36mCost:\033[0m      {cost_str}")
    print(f"  \033[36mCommands:\033[0m  \033[31mexit\033[0m · \033[31m/clear\033[0m · \033[31m/stats\033[0m · \033[31m/help\033[0m")
    if CFG.provider == "openai":
        print("  \033[36mTry:\033[0m      \033[31m/weather\033[0m for function calling demo")
    if CFG.history:
        print(f"  \033[36mHistory:\033[0m  {CFG.history} ({len(messages)} msgs loaded)")
    print("")

    # ── Input loop ────────────────────────────────────────────
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                user_input = (await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("\033[36mYou:\033[0m ").strip()
                ))
            except (EOFError, KeyboardInterrupt):
                print("\n\033[32m👋 Bye!\033[0m")
                if CFG.history:
                    save_history(CFG.history, messages)
                break

            if not user_input:
                continue

            # ── Commands ──────────────────────────────────────
            if user_input.lower() in ("exit", "/exit"):
                print("\n\033[32m👋 Bye!\033[0m")
                if CFG.history:
                    save_history(CFG.history, messages)
                break

            if user_input.lower() == "/clear":
                messages.clear()
                print("\033[33m🧹 History cleared.\033[0m\n")
                continue

            if user_input.lower() == "/stats":
                print("")
                print("  \033[33mSession Stats:\033[0m")
                print(f"  Queries:      {query_count}")
                print(f"  Tokens in:    {total_tokens_in}")
                print(f"  Tokens out:   {total_tokens_out}")
                print(f"  Total cost:   ${total_cost:.6f}")
                avg_lat = total_latency / (query_count * 1000) if query_count > 0 else 0
                print(f"  Avg latency:  {avg_lat:.1f}s")
                print(f"  History len:  {len(messages)} messages")
                print("")
                continue

            if user_input.lower() == "/help":
                print("")
                print("  \033[33mCommands:\033[0m")
                print("  \033[36mexit\033[0m         Exit")
                print("  \033[36m/clear\033[0m       Clear history")
                print("  \033[36m/stats\033[0m       Session statistics")
                print("  \033[36m/help\033[0m        This help")
                if CFG.provider == "openai":
                    print("  \033[36m/weather\033[0m    Function calling demo")
                print("")
                continue

            if user_input.lower().startswith("/save "):
                file_path = user_input[6:].strip()
                if file_path:
                    save_history(file_path, messages)
                    print(f"\033[32m✓ History saved to {file_path}\033[0m\n")
                continue

            if user_input.lower().startswith("/load "):
                file_path = user_input[6:].strip()
                if file_path:
                    messages = load_history(file_path)
                continue

            # ── Weather demo ─────────────────────────────────
            if user_input.lower() == "/weather" and CFG.provider == "openai":
                messages.append({
                    "role": "user",
                    "content": "What's the weather like in Tokyo and New York?"
                })
            else:
                messages.append({"role": "user", "content": user_input})

            # ── Stream ──────────────────────────────────────
            print(f"\033[33m{provider['name']}:\033[0m ", end="", flush=True)
            start = time.monotonic()
            query_count += 1

            try:
                full_reply = ""
                async for token in stream_response(session, provider, model, messages):
                    print(token, end="", flush=True)
                    full_reply += token

                print("")  # newline after stream

                # Token tracking (approximate if no API data)
                in_tokens = count_message_tokens(messages)
                out_tokens = count_tokens(full_reply)
                total_tokens_in += in_tokens
                total_tokens_out += out_tokens
                query_cost = (
                    (in_tokens / 1_000_000) * provider["cost_per_1m_in"] +
                    (out_tokens / 1_000_000) * provider["cost_per_1m_out"]
                )
                total_cost += query_cost

                elapsed = time.monotonic() - start
                total_latency += elapsed * 1000

                messages.append({"role": "assistant", "content": full_reply})

                print(
                    f"\033[90m  ── {provider['name']} · {model} · "
                    f"{elapsed:.1f}s · ${total_cost:.6f} session · "
                    f"{query_count} queries\033[0m\n"
                )

            except Exception as e:
                print("")
                _log("error", f"Request failed: {e}")
                print(f"\033[90m  ── failed after {CFG.retry_max} retries\033[0m\n")


# ═════════════════════════════════════════════════════════════════════
# 11. ENTRY POINT
# ═════════════════════════════════════════════════════════════════════

def main():
    print(f"\033[32m🚀 Production CLI Bot v2 — Day 8\033[0m")
    print(f"   Provider: {CFG.provider} · Stream: {'ON' if not CFG.no_stream else 'OFF'}")
    print(f"   Log level: {CFG.log_level} · Max retries: {CFG.retry_max}\n")

    try:
        asyncio.run(chat())
    except KeyboardInterrupt:
        print("\n\033[32m👋 Bye!\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()

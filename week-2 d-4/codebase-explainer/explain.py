#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────
# Day 9 / Week 2 Day 4 — Codebase Explainer Tool (Python)
#
# Explains a codebase using an LLM, staying within 10K tokens per query.
# Supports Anthropic (with prompt caching) and OpenAI.
#
# Usage:
#   python explain.py <directory>
#   python explain.py <directory> --provider openai
#   python explain.py <directory> --max-tokens 5000
#   python explain.py <directory> --output summary.md
#
# Environment:
#   ANTHROPIC_API_KEY  — required for Anthropic/Claude
#   OPENAI_API_KEY     — required for OpenAI
# ─────────────────────────────────────────────────────────────────────

import argparse
import json
import os
import pathlib
import sys
import time
from urllib import request, error

# ═════════════════════════════════════════════════════════════════════
# 1. CONFIG
# ═════════════════════════════════════════════════════════════════════

parser = argparse.ArgumentParser(description="Codebase Explainer Tool")
parser.add_argument("directory", nargs="?", default=".", help="Directory to explain")
parser.add_argument("--provider", default="anthropic", choices=["anthropic", "openai"])
parser.add_argument("--max-tokens", type=int, default=int(os.getenv("EXPLAIN_MAX_TOKENS", "10000")))
parser.add_argument("--output", default=None, help="Save explanation to file")
parser.add_argument("--verbose", action="store_true", help="Show file list")
args = parser.parse_args()

TARGET_DIR = pathlib.Path(args.directory).resolve()
DIR_NAME = TARGET_DIR.name

# ═════════════════════════════════════════════════════════════════════
# 2. FILE SCANNER
# ═════════════════════════════════════════════════════════════════════

IGNORED_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", "out",
    "__pycache__", ".cache", ".venv", "venv", "env", ".env",
    "coverage", ".nyc_output", ".turbo", ".tsbuildinfo",
}

SOURCE_EXTS = {
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".py", ".rb", ".go", ".rs", ".java", ".kt", ".swift",
    ".css", ".scss", ".less", ".html", ".htm", ".xml",
    ".json", ".yaml", ".yml", ".toml", ".md", ".sql",
    ".sh", ".bash", ".zsh", ".env.example",
    ".vue", ".svelte", ".astro",
}

NAMED_FILES = {
    "Dockerfile", "Makefile", "docker-compose.yml",
    "docker-compose.yaml", ".gitignore", ".env.example",
    "package.json", "tsconfig.json", "vite.config.js",
    "vite.config.ts", "next.config.js", "webpack.config.js",
    "requirements.txt", "Pipfile", "Gemfile", "Cargo.toml",
    "go.mod", "pom.xml", "build.gradle",
}


def scan_directory(dir_path: pathlib.Path):
    files = []
    for entry in dir_path.rglob("*"):
        if entry.is_dir():
            continue
        if any(ignored in entry.parts for ignored in IGNORED_DIRS):
            continue
        if entry.suffix.lower() in SOURCE_EXTS or entry.name in NAMED_FILES:
            files.append(entry)
    return sorted(files)


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def read_files_with_budget(files, budget_tokens: int):
    total_tokens = 0
    results = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        file_tokens = estimate_tokens(content)
        rel_path = str(file_path.relative_to(TARGET_DIR))

        if total_tokens + file_tokens > budget_tokens:
            remaining = budget_tokens - total_tokens
            max_chars = remaining * 4
            truncated = content[:max_chars]
            results.append({
                "path": rel_path,
                "content": truncated,
                "truncated": True,
                "tokens": remaining,
            })
            total_tokens += remaining
            break

        results.append({
            "path": rel_path,
            "content": content,
            "truncated": False,
            "tokens": file_tokens,
        })
        total_tokens += file_tokens

    return results, total_tokens


# ═════════════════════════════════════════════════════════════════════
# 3. LLM CALLERS
# ═════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """You are a senior software engineer reviewing a codebase. 
Your task is to explain what this codebase does, its architecture, key technologies, 
and notable patterns. Be concise but thorough. Focus on:
1. Overall purpose of the project
2. Tech stack and key dependencies
3. Architecture and component structure
4. Notable patterns, conventions, or design decisions
5. Entry points and how to run the project

Format your response in Markdown with clear sections."""


def build_code_context(files, dir_name):
    ctx = f"# Codebase: {dir_name}\n\n"
    for f in files:
        ctx += f"## File: {f['path']}\n```\n{f['content']}\n```\n"
        if f["truncated"]:
            ctx += "\n*(file truncated to fit token budget)*\n"
    return ctx


def call_anthropic(code_context):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    body = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
        "system": [
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": code_context,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
        ],
    }).encode("utf-8")

    req = request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "anthropic-beta": "prompt-caching-2024-07-31",
        },
        method="POST",
    )

    try:
        resp = request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API error {e.code}: {err_body[:300]}")

    text = ""
    if data.get("content"):
        for block in data["content"]:
            if block.get("type") == "text":
                text += block.get("text", "")

    usage = data.get("usage", {})
    return {
        "text": text,
        "usage": {
            "in": usage.get("input_tokens", 0),
            "out": usage.get("output_tokens", 0),
            "cache_creation": usage.get("cache_creation_input_tokens", 0),
            "cache_read": usage.get("cache_read_input_tokens", 0),
        },
    }


def call_openai(code_context):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": code_context},
        ],
        "max_tokens": 4096,
    }).encode("utf-8")

    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        resp = request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {e.code}: {err_body[:300]}")

    usage = data.get("usage", {})
    return {
        "text": data.get("choices", [{}])[0].get("message", {}).get("content", ""),
        "usage": {
            "in": usage.get("prompt_tokens", 0),
            "out": usage.get("completion_tokens", 0),
            "cache_creation": 0,
            "cache_read": 0,
        },
    }


# ═════════════════════════════════════════════════════════════════════
# 4. MAIN
# ═════════════════════════════════════════════════════════════════════

def main():
    print(f"\033[32m🔍 Codebase Explainer — Day 9\033[0m")
    print(f"   \033[36mDirectory:\033[0m  {TARGET_DIR}")
    print(f"   \033[36mProvider:\033[0m   {args.provider}")
    print(f"   \033[36mMax tokens:\033[0m {args.max_tokens:,}\n")

    # Scan
    print("\033[36m📂 Scanning files...\033[0m")
    all_files = scan_directory(TARGET_DIR)
    print(f"   Found {len(all_files)} source files\n")

    if not all_files:
        print(f"\033[33mNo source files found\033[0m")
        return

    # Read within budget
    print(f"\033[36m📖 Reading files (budget: {args.max_tokens:,} tokens)...\033[0m")
    file_data, total_tokens = read_files_with_budget(all_files, args.max_tokens)
    print(f"   Read {len(file_data)} files ({total_tokens:,} tokens)")
    if len(file_data) < len(all_files):
        print(f"   \033[33m   {len(all_files) - len(file_data)} files excluded to stay within budget\033[0m")

    if args.verbose:
        print("")
        print("  \033[90mFiles included:\033[0m")
        for f in file_data:
            flag = " \033[33m(truncated)\033[0m" if f["truncated"] else ""
            print(f"    \033[90m- {f['path']} ({f['tokens']} tokens){flag}\033[0m")
        print("")

    # Call LLM
    provider_name = "Claude (with prompt caching)" if args.provider == "anthropic" else "GPT-4o-mini"
    print(f"\033[36m🤖 Asking {provider_name}...\033[0m\n")

    code_context = build_code_context(file_data, DIR_NAME)
    start = time.time()

    try:
        if args.provider == "anthropic":
            result = call_anthropic(code_context)
        else:
            result = call_openai(code_context)
    except RuntimeError as e:
        print(f"\033[31m✗ Error: {e}\033[0m")
        sys.exit(1)

    elapsed = time.time() - start

    # Output
    output = result["text"]
    print(output)
    print("")

    # Telemetry
    in_tokens = result["usage"]["in"]
    out_tokens = result["usage"]["out"]
    cost_rates = {
        "anthropic": {"in": 3.0, "out": 15.0},
        "openai": {"in": 0.15, "out": 0.60},
    }
    rates = cost_rates.get(args.provider, cost_rates["openai"])
    cost = (in_tokens / 1_000_000) * rates["in"] + (out_tokens / 1_000_000) * rates["out"]

    print(f"\033[90m  ───────────────────────────────────────────────\033[0m")
    print(f"\033[90m  Provider:  {args.provider}\033[0m")
    print(f"\033[90m  Tokens in: {in_tokens:,}\033[0m")
    print(f"\033[90m  Tokens out: {out_tokens:,}\033[0m")
    print(f"\033[90m  Cost:      ${cost:.6f}\033[0m")
    print(f"\033[90m  Time:      {elapsed:.1f}s\033[0m")
    if result["usage"]["cache_read"] > 0:
        print(f"\033[90m  Cache read: {result['usage']['cache_read']} tokens (saved ${result['usage']['cache_read'] / 1_000_000 * rates['in']:.6f})\033[0m")
    print("")

    # Save to file
    if args.output:
        pathlib.Path(args.output).write_text(output, encoding="utf-8")
        print(f"\033[32m✓ Saved explanation to {args.output}\033[0m\n")


if __name__ == "__main__":
    main()

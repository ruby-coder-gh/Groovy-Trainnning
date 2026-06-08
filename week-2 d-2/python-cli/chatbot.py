#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────
# Day 7 / Week 2 Day 2 — Multi-Provider CLI Chatbot (Python)
# OpenAI · Gemini · Ollama  (switch via --provider flag)
#
# Usage:
#   python chatbot.py                          # default: ollama
#   python chatbot.py --provider openai
#   python chatbot.py --provider gemini
#   python chatbot.py --provider ollama
#   python chatbot.py --provider openai --model gpt-4o-mini
#
# Environment variables (optional per provider):
#   OPENAI_API_KEY    — required for OpenAI
#   GEMINI_API_KEY    — required for Gemini
# ─────────────────────────────────────────────────────────────────────

import json
import os
import sys
import time
from urllib import request, error

# ─── Parse CLI args ───────────────────────────────────────────────
PROVIDER = "ollama"
MODEL_OVERRIDE = None

args = sys.argv[1:]
for i, arg in enumerate(args):
    if arg == "--provider" and i + 1 < len(args):
        PROVIDER = args[i + 1].lower()
    elif arg == "--model" and i + 1 < len(args):
        MODEL_OVERRIDE = args[i + 1]


# ─── Provider configs ─────────────────────────────────────────────
def _build_openai_payload(messages, model, functions=None):
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if functions:
        payload["functions"] = functions
        payload["function_call"] = "auto"
    return payload


def _build_gemini_payload(messages):
    contents = []
    for m in messages:
        role = "model" if m["role"] == "assistant" else m["role"]
        contents.append({
            "role": role,
            "parts": [{"text": m["content"]}]
        })
    return {"contents": contents}


def _build_ollama_payload(messages, model):
    return {"model": model, "messages": messages, "stream": False}


PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o-mini",
        "url": "https://api.openai.com/v1/chat/completions",
        "build_payload": _build_openai_payload,
        "parse_response": lambda data: data["choices"][0]["message"]["content"],
        "parse_usage": lambda data: {
            "in": data["usage"]["prompt_tokens"],
            "out": data["usage"]["completion_tokens"],
        } if "usage" in data else None,
        "cost_per_1m_in": 0.15,
        "cost_per_1m_out": 0.60,
        "functions": [
            {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"},
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["city"],
                },
            },
        ],
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
            f"{model}:generateContent?key={os.environ.get('GEMINI_API_KEY', '')}"
        ),
        "build_payload": _build_gemini_payload,
        "parse_response": lambda data: (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "(no response)")
        ),
        "parse_usage": lambda data: {
            "in": data.get("usageMetadata", {}).get("promptTokenCount", 0),
            "out": data.get("usageMetadata", {}).get("candidatesTokenCount", 0),
        } if "usageMetadata" in data else None,
        "cost_per_1m_in": 0.075,
        "cost_per_1m_out": 0.30,
        "headers": lambda: {"Content-Type": "application/json"},
    },
    "ollama": {
        "name": "Ollama",
        "default_model": "qwen3:8b",
        "url": "http://localhost:11434/api/chat",
        "build_payload": lambda msgs, model: {
            "model": model, "messages": msgs, "stream": False,
        },
        "parse_response": lambda data: data.get("message", {}).get("content", "(no response)"),
        "parse_usage": lambda data: {
            "in": data.get("prompt_eval_count", 0),
            "out": data.get("eval_count", 0),
        } if "prompt_eval_count" in data else None,
        "cost_per_1m_in": 0,
        "cost_per_1m_out": 0,
        "headers": lambda: {"Content-Type": "application/json"},
    },
}

# ─── Validate provider ────────────────────────────────────────────
if PROVIDER not in PROVIDERS:
    print(f"\033[31mUnknown provider: '{PROVIDER}'. Use --provider openai | gemini | ollama\033[0m")
    sys.exit(1)

provider = PROVIDERS[PROVIDER]
MODEL = MODEL_OVERRIDE or provider["default_model"]

if PROVIDER == "openai" and not os.environ.get("OPENAI_API_KEY"):
    print("\033[33m⚠  OPENAI_API_KEY not set. Set it via: export OPENAI_API_KEY=sk-...\033[0m")

if PROVIDER == "gemini" and not os.environ.get("GEMINI_API_KEY"):
    print("\033[33m⚠  GEMINI_API_KEY not set. Set it via: export GEMINI_API_KEY=...\033[0m")

# ─── Conversation history ────────────────────────────────────────
messages = []


def execute_function(fn_call):
    """Simulated function execution for OpenAI function calling demo."""
    name = fn_call["name"]
    args = json.loads(fn_call.get("arguments", "{}"))
    print(f"\033[35m⚡ Function called: {name}({json.dumps(args)})\033[0m")

    if name == "get_weather":
        conditions = ["Sunny ☀️", "Cloudy ☁️", "Rainy 🌧️", "Windy 💨"]
        import random
        return {
            "city": args.get("city", "Unknown"),
            "temperature": 72 if args.get("unit") == "fahrenheit" else 22,
            "unit": args.get("unit", "celsius"),
            "condition": random.choice(conditions),
            "humidity": f"{random.randint(40, 80)}%",
        }
    return {"result": f"Function {name} executed (simulated)"}


def call_provider(messages):
    """Send messages to the selected provider and return response text."""
    if isinstance(provider["url"], str):
        url = provider["url"]
    else:
        url = provider["url"](MODEL)

    # Build payload — OpenAI gets functions attached
    if PROVIDER == "openai":
        payload = provider["build_payload"](messages, MODEL, provider.get("functions"))
    else:
        payload = provider["build_payload"](messages, MODEL)

    data_bytes = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data_bytes, headers=provider["headers"](), method="POST")

    try:
        resp = request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{provider['name']} API error {e.code}: {body}")
    except error.URLError as e:
        raise RuntimeError(f"Connection error: {e.reason}")

    # Handle OpenAI function calling
    if PROVIDER == "openai":
        choice = data.get("choices", [{}])[0]
        if choice.get("finish_reason") == "function_call":
            fn_call = choice["message"]["function_call"]
            result = execute_function(fn_call)

            # Append function call + result to history
            messages.append({
                "role": "assistant",
                "content": None,
                "function_call": {"name": fn_call["name"], "arguments": fn_call["arguments"]},
            })
            messages.append({
                "role": "function",
                "name": fn_call["name"],
                "content": json.dumps(result),
            })

            # Re-call without functions to get text
            clean_payload = {
                "model": MODEL,
                "messages": [
                    {k: v for k, v in m.items() if k != "function_call"}
                    if m.get("role") == "assistant" else m
                    for m in messages
                ],
                "stream": False,
            }
            data_bytes = json.dumps(clean_payload).encode("utf-8")
            req = request.Request(url, data=data_bytes, headers=provider["headers"](), method="POST")
            resp = request.urlopen(req, timeout=120)
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    return provider["parse_response"](data)


def format_cost(usage):
    """Format token usage and cost."""
    if not usage:
        return ""
    in_cost = (usage["in"] / 1_000_000) * provider["cost_per_1m_in"]
    out_cost = (usage["out"] / 1_000_000) * provider["cost_per_1m_out"]
    total = in_cost + out_cost
    return f" [in: {usage['in']} · out: {usage['out']} · ${total:.6f}]"


# ─── Chat loop ──────────────────────────────────────────────────
def chat():
    print("")
    print("\033[32m╔══════════════════════════════════════════════╗\033[0m")
    print("\033[32m║   🚀 Multi-Provider CLI Chatbot — Day 7     ║\033[0m")
    print("\033[32m╚══════════════════════════════════════════════╝\033[0m")
    print(f"  \033[36mProvider:\033[0m  {provider['name']}")
    print(f"  \033[36mModel:\033[0m     {MODEL}")
    cost_str = "Free (local)" if provider["cost_per_1m_in"] == 0 else \
        f"${provider['cost_per_1m_in']}/1M in · ${provider['cost_per_1m_out']}/1M out"
    print(f"  \033[36mCost:\033[0m      {cost_str}")
    print("  Type \033[31mexit\033[0m to quit · \033[31m/clear\033[0m to reset · \033[31m/help\033[0m for commands")
    if PROVIDER == "openai":
        print("  Try \033[31m/weather\033[0m to see function calling in action")
    print("")

    while True:
        try:
            user_input = input("\033[36mYou:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\033[32m👋 Bye!\033[0m")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("\n\033[32m👋 Bye!\033[0m")
            break

        if user_input.lower() == "/clear":
            messages.clear()
            print("\033[33m🧹 History cleared.\033[0m\n")
            continue

        if user_input.lower() == "/help":
            print("")
            print("  \033[33mCommands:\033[0m")
            print("  \033[36mexit\033[0m        Exit the chatbot")
            print("  \033[36m/clear\033[0m      Clear conversation history")
            print("  \033[36m/help\033[0m       Show this help")
            if PROVIDER == "openai":
                print("  \033[36m/weather\033[0m    Try function calling (simulated weather)")
            print("")
            continue

        # OpenAI function calling demo
        if user_input.lower() == "/weather" and PROVIDER == "openai":
            messages.append({
                "role": "user",
                "content": "What's the weather like in Tokyo and New York?"
            })
        else:
            messages.append({"role": "user", "content": user_input})

        print(f"\033[33m{provider['name']}:\033[0m ", end="", flush=True)
        start = time.time()

        try:
            reply = call_provider(messages)
            elapsed = time.time() - start
            print(reply)
            messages.append({"role": "assistant", "content": reply})
            print(f"\033[90m  ── {provider['name']} · {MODEL} · {elapsed:.1f}s\033[0m\n")
        except Exception as e:
            print("")
            print(f"\033[31m  ✗ Error:\033[0m {e}\n")


if __name__ == "__main__":
    chat()

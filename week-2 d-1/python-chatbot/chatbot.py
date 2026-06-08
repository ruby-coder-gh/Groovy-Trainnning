# ──────────────────────────────────────────────────────────
# Ollama CLI Chatbot — Python
# Multi-turn conversation with history maintained
# Uses 'requests' — pip install requests
# ──────────────────────────────────────────────────────────

import json
import sys
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"

# ─── Conversation history ────────────────────────────────
messages = []

# ─── Call Ollama ─────────────────────────────────────────
def ask_ollama(messages):
    payload = {"model": MODEL, "messages": messages, "stream": False}
    res = requests.post(OLLAMA_URL, json=payload, timeout=120)
    res.raise_for_status()
    return res.json()["message"]["content"]

# ─── Chat loop ──────────────────────────────────────────
def chat():
    print(f"\n\033[32m🚀 Ollama CLI Chatbot\033[0m")
    print(f"   Model: {MODEL}")
    print("   Type \033[31mexit\033[0m to quit · \033[31m/clear\033[0m to reset\n")

    while True:
        try:
            user_input = input("\033[36mYou:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Bye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("\n👋 Bye!")
            break

        if user_input.lower() == "/clear":
            messages.clear()
            print("🧹 History cleared.\n")
            continue

        messages.append({"role": "user", "content": user_input})

        try:
            print(f"\033[33mOllama:\033[0m ", end="", flush=True)
            reply = ask_ollama(messages)
            print(reply)
            messages.append({"role": "assistant", "content": reply})
            print()
        except Exception as e:
            print(f"\033[31mError:\033[0m {e}\n")


if __name__ == "__main__":
    chat()

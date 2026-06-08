# ──────────────────────────────────────────────────────────
# Anthropic CLI Chatbot — Python SDK
# Multi-turn conversation with history maintained
# ──────────────────────────────────────────────────────────

import os
import sys
from anthropic import Anthropic

MODEL = "claude-sonnet-4-20250514"

# ─── Setup ───────────────────────────────────────────────
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ANTHROPIC_API_KEY environment variable is required")
    sys.exit(1)

client = Anthropic(api_key=api_key)

# ─── Conversation history ────────────────────────────────
messages = []

# ─── Chat loop ──────────────────────────────────────────
def chat():
    print("\n\033[32m🚀 Anthropic CLI Chatbot\033[0m")
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

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=512,
                messages=messages,
            )

            reply = response.content[0].text
            print(f"\033[33mClaude:\033[0m {reply}")

            # Add assistant response to history
            messages.append({"role": "assistant", "content": reply})

            usage = response.usage
            print(
                f"\033[90m╰─ tokens: {usage.input_tokens} in · {usage.output_tokens} out\033[0m\n"
            )

        except Exception as e:
            print(f"\033[31mError:\033[0m {e}\n")


if __name__ == "__main__":
    chat()

"""
🧠 Short-Term Memory — Conversation Buffer

Part 5 of Day 14 — Keeps track of the current conversation.
Sliding window: keeps the last N messages so the LLM fits in context.
"""

from typing import List, Dict, Optional


class ShortTermMemory:
    """
    Sliding-window conversation buffer.

    Stores messages and returns the last `window_size` messages
    when building context for the LLM.
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.messages: List[Dict[str, str]] = []

    def add_user(self, content: str) -> None:
        """Add a user message to memory."""
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant(self, content: str) -> None:
        """Add an assistant message to memory."""
        self.messages.append({"role": "assistant", "content": content})
        self._trim()

    def add_tool(self, content: str, tool_call_id: str) -> None:
        """Add a tool result message to memory."""
        self.messages.append({"role": "tool", "content": content, "tool_call_id": tool_call_id})
        self._trim()

    def add_system(self, content: str) -> None:
        """Add a system message (always kept at position 0)."""
        # Insert system message at the beginning if it doesn't exist
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0] = {"role": "system", "content": content}
        else:
            self.messages.insert(0, {"role": "system", "content": content})

    def get_context(self) -> List[Dict[str, str]]:
        """
        Return the messages to send to the LLM.
        System message (if any) is always included, plus the last window_size messages.
        """
        if not self.messages:
            return []

        # Separate system message
        system_msgs = [m for m in self.messages if m.get("role") == "system"]
        other_msgs = [m for m in self.messages if m.get("role") != "system"]

        # Take last window_size non-system messages
        recent = other_msgs[-self.window_size:] if len(other_msgs) > self.window_size else other_msgs

        return system_msgs + recent

    def get_history(self) -> List[Dict[str, str]]:
        """Return all stored messages."""
        return self.messages

    def clear(self) -> None:
        """Clear all messages."""
        self.messages = []

    def count_messages(self) -> int:
        """Count total messages stored."""
        return len(self.messages)

    def _trim(self) -> None:
        """Trim old non-system messages when exceeding window."""
        if self.messages:
            system_msgs = [m for m in self.messages if m.get("role") == "system"]
            other_msgs = [m for m in self.messages if m.get("role") != "system"]

            # Keep system messages + last window_size * 2 (to account for turns)
            max_other = self.window_size * 3
            if len(other_msgs) > max_other:
                other_msgs = other_msgs[-max_other:]

            self.messages = system_msgs + other_msgs

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        roles = [m.get("role", "?")[:1] for m in self.messages]
        return f"ShortTermMemory({len(self.messages)} msgs: {''.join(roles)})"


# ──────────────────────────────────────────────
# Demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("🧠 Short-Term Memory Demo")
    print("-" * 40)

    mem = ShortTermMemory(window_size=4)

    mem.add_system("You are a helpful assistant.")
    mem.add_user("What is AI?")
    mem.add_assistant("AI is artificial intelligence.")
    mem.add_user("Explain machine learning.")
    mem.add_assistant("ML is a subset of AI.")

    print(f"Memory: {mem}")
    print(f"Context ({len(mem.get_context())} msgs):")
    for m in mem.get_context():
        print(f"  [{m['role']}]: {m['content'][:50]}...")

    print("\n--- Adding more to trigger trim ---")
    for i in range(5):
        mem.add_user(f"Message {i}")
        mem.add_assistant(f"Response {i}")

    print(f"Memory: {mem}")
    print(f"Context messages: {len(mem.get_context())}")
    for m in mem.get_context():
        role = m['role']
        content = m['content'][:40]
        print(f"  [{role}]: {content}")

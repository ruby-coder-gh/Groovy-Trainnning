"""
🤖 Pure SDK Agent — Google Gemini (No Framework)
Part 3 of Day 14 — The real agent loop, no abstractions.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# ──────────────────────────────────────────────
# TOOL IMPLEMENTATIONS
# ──────────────────────────────────────────────

def calculator(a: float, b: float, operation: str) -> float:
    ops = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Error: division by zero",
    }
    return ops.get(operation, f"Error: unknown operation '{operation}'")

def current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def reverse_string(text: str) -> str:
    return text[::-1]

def word_count(text: str) -> int:
    return len(text.split())

# Web search
try:
    from ddgs import DDGS
    def web_search(query: str, max_results: int = 3) -> str:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        if not results:
            return "No results found"
        return "\n\n".join(
            f"{i+1}. {r['title']}: {r['body'][:200]}"
            for i, r in enumerate(results)
        )
except:
    def web_search(query: str, max_results: int = 3) -> str:
        return "Web search unavailable (install ddgs)"

# ──────────────────────────────────────────────
# TOOL SCHEMAS (Gemini FunctionDeclarations)
# ──────────────────────────────────────────────

FUNCTION_DECLARATIONS = [
    {
        "name": "calculator",
        "description": "Perform basic math: add, subtract, multiply, divide",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "Math operation",
                },
            },
            "required": ["a", "b", "operation"],
        },
    },
    {
        "name": "current_time",
        "description": "Get the current date and time",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "reverse_string",
        "description": "Reverse any text string",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to reverse"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the internet for current information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "word_count",
        "description": "Count the number of words in a text",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to count words in"},
            },
            "required": ["text"],
        },
    },
]

# Tool dispatch map
TOOL_FUNCTIONS = {
    "calculator": calculator,
    "current_time": current_time,
    "reverse_string": reverse_string,
    "web_search": web_search,
    "word_count": word_count,
}

def execute_tool(name: str, args: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return f"Error: unknown tool '{name}'"
    try:
        result = fn(**args)
        return str(result)
    except Exception as e:
        return f"Error: {e}"

# ──────────────────────────────────────────────
# AGENT LOOP (the heart — same as all frameworks)
# ──────────────────────────────────────────────

def agent_loop(user_query: str, max_turns: int = 5, verbose: bool = True) -> str:
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_query)])]

    tools = types.Tool(function_declarations=FUNCTION_DECLARATIONS)

    for turn in range(max_turns):
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=[tools],
                temperature=0,
            ),
        )

        if not response.candidates:
            return "No response from model"

        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        # Check if it's a function call
        if part.function_call:
            fc = part.function_call
            name = fc.name
            args = {k: v for k, v in fc.args.items()}
            result = execute_tool(name, args)

            if verbose:
                print(f"  🔧 Turn {turn+1}: {name}({json.dumps(args)}) \u2192 {result[:80]}")

            # Add model's original function call to history (preserves thought_signature)
            contents.append(types.Content(
                role="model",
                parts=[candidate.content.parts[0]],
            ))
            # Add function response
            contents.append(types.Content(
                role="user",  # Gemini uses "user" role for function responses
                parts=[types.Part.from_function_response(
                    name=name,
                    response={"result": result},
                )],
            ))
        else:
            # Text response = final answer
            return part.text if part.text else "No response"

    return "Max turns reached without final answer."

# ── CLI ────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", type=str, help="Single query")
    parser.add_argument("-v", "--verbose", action="store_true", default=True)
    args = parser.parse_args()

    if args.query:
        print(agent_loop(args.query, verbose=args.verbose))
    else:
        print("\n=== Pure SDK Agent (Gemini \u2014 No Framework) ===")
        print("This is the SAME loop LangChain/LlamaIndex use internally")
        print("Type 'exit' to quit\n")
        while True:
            try:
                q = input("You: ").strip()
                if q.lower() in ("exit", "quit", "q"):
                    break
                if not q:
                    continue
                result = agent_loop(q, verbose=True)
                print(f"\nAgent: {result}\n")
            except (EOFError, KeyboardInterrupt):
                break
        print("Bye!")

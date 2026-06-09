import os
import sys
import argparse
from dotenv import load_dotenv

load_dotenv()

# ── Gemini via LangChain ─────────────────────
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import create_agent

# ── Tools ──────────────────────────────────────────

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression like '25 * 18' or '15 + 37'."""
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "Error: invalid characters"
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

@tool
def current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def reverse_string(text: str) -> str:
    """Reverse any string. Input: the string to reverse."""
    return text[::-1]

tools = [calculator, current_time, reverse_string]

try:
    from langchain_community.tools import DuckDuckGoSearchRun
    search = DuckDuckGoSearchRun()
    @tool
    def web_search(query: str) -> str:
        """Search the web for current information. Input: a search query."""
        return search.run(query)
    tools.append(web_search)
except:
    pass

# ── Agent Setup (Gemini + LangChain) ─────────

llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0,
)

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="You are a helpful assistant with access to tools. Use them to answer questions accurately.",
    debug=True,
)

def run_query(query: str) -> str:
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})
        return result["messages"][-1].content
    except Exception as e:
        return f"Error: {e}"

# ── CLI ────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", type=str, help="Single query mode")
    args = parser.parse_args()

    if args.query:
        print(run_query(args.query))
    else:
        print("\n=== LangChain Agent (Gemini) ===")
        print("Type your query, or 'exit' to quit\n")
        while True:
            try:
                q = input("You: ").strip()
                if q.lower() in ("exit", "quit", "q"):
                    break
                if not q:
                    continue
                print(f"\nAgent: {run_query(q)}\n")
            except (EOFError, KeyboardInterrupt):
                break
        print("Bye!")

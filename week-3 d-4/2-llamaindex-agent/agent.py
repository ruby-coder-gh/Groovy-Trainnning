import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# ── Document Index ─────────────────────────────────
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

api_key = os.getenv("GOOGLE_API_KEY")
model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

Settings.llm = Gemini(
    model=model,
    api_key=api_key,
    temperature=0,
)
# Use local HuggingFace embeddings (no API key needed, no quota limits)
Settings.embed_model = HuggingFaceEmbedding(
    model_name="all-MiniLM-L6-v2",
)

# Load and index the sample doc
doc_dir = Path(__file__).parent / "data"
if doc_dir.exists():
    docs = SimpleDirectoryReader(str(doc_dir)).load_data()
    index = VectorStoreIndex.from_documents(docs)
    query_engine = index.as_query_engine()
else:
    query_engine = None

def query_document(query: str) -> str:
    """Answer questions based on the loaded documents."""
    if query_engine is None:
        return "No documents loaded."
    try:
        response = query_engine.query(query)
        return str(response)
    except Exception as e:
        return f"Error: {e}"

# ── Calculator Tool ────────────────────────────────
from llama_index.core.tools import FunctionTool

def calculator(a: float, b: float, operation: str) -> float:
    """Perform basic arithmetic."""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    else:
        raise ValueError(f"Unknown operation: {operation}")

calc_tool = FunctionTool.from_defaults(fn=calculator)

# ── Agent Setup ────────────────────────────────────
from llama_index.core.agent import ReActAgent

agent = ReActAgent(
    tools=[calc_tool],
    llm=Settings.llm,
    verbose=True,
)

async def _run_agent_async(query: str) -> str:
    """Call agent.run() inside a running event loop (required by workflows)."""
    handler = agent.run(query)
    result = await handler
    return str(result)

def run_query(query: str) -> str:
    """Try RAG query first, fall back to agent."""
    calc_keywords = ["calculate", "multiply", "add", "subtract", "divide", "*", "+", "-", "/"]
    is_calc = any(kw in query.lower() for kw in calc_keywords)

    if not is_calc:
        return query_document(query)

    try:
        return asyncio.run(_run_agent_async(query))
    except Exception as e:
        return f"Agent error: {e}"

# ── CLI ────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", "--query", type=str, help="Single query")
    args = parser.parse_args()

    if args.query:
        print(run_query(args.query))
    else:
        print("\n=== LlamaIndex Agent (Gemini) ===")
        print("Ask about the document or do calculations")
        print("Type 'exit' to quit\n")
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

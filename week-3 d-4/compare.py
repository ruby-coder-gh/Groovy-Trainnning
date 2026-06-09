#!/usr/bin/env python3
"""
📊 Comparison Runner — LangChain vs LlamaIndex vs Pure SDK

Runs the same query through all 3 agent frameworks and compares
the results, speed, and approach.

Part 4 of Day 14 — Understanding that all frameworks are just
wrappers around the same agent loop.
"""

import os
import sys
import time
import json
import importlib.util
from dotenv import load_dotenv

load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))

def _import_from_path(module_name: str, file_path: str):
    """Safely import a module from a specific file path using importlib."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    # Keep a cache so repeated calls return the same module
    if module_name not in sys.modules:
        sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

# ──────────────────────────────────────────────
# Test Queries
# ──────────────────────────────────────────────

TEST_QUERIES = [
    ("🧮 Calculator", "What is 25 multiplied by 18?"),
    ("🔄 Multi-step", "What is 15 + 37 and then multiply the result by 2?"),
    ("⏰ Time", "What time is it right now?"),
    ("🔄 String", "Reverse the word 'artificial'"),
]


def run_langchain(query: str) -> dict:
    """Run query through LangChain agent."""
    mod = _import_from_path("lc_agent", os.path.join(HERE, "1-langchain-agent", "agent.py"))
    start = time.time()
    try:
        result = mod.run_query(query)
        elapsed = time.time() - start
        return {"result": str(result)[:200], "time": round(elapsed, 2), "error": None}
    except Exception as e:
        elapsed = time.time() - start
        return {"result": None, "time": round(elapsed, 2), "error": str(e)[:200]}


def run_llamaindex(query: str) -> dict:
    """Run query through LlamaIndex agent."""
    mod = _import_from_path("li_agent", os.path.join(HERE, "2-llamaindex-agent", "agent.py"))
    start = time.time()
    try:
        result = mod.run_query(query)
        elapsed = time.time() - start
        return {"result": str(result)[:200], "time": round(elapsed, 2), "error": None}
    except Exception as e:
        elapsed = time.time() - start
        return {"result": None, "time": round(elapsed, 2), "error": str(e)[:200]}


def run_pure_sdk(query: str) -> dict:
    """Run query through Pure SDK agent."""
    mod = _import_from_path("ps_agent", os.path.join(HERE, "3-pure-sdk-agent", "agent.py"))
    start = time.time()
    try:
        result = mod.agent_loop(query, verbose=False)
        elapsed = time.time() - start
        return {"result": str(result)[:200], "time": round(elapsed, 2), "error": None}
    except Exception as e:
        elapsed = time.time() - start
        return {"result": None, "time": round(elapsed, 2), "error": str(e)[:200]}


# ──────────────────────────────────────────────
# Comparison
# ──────────────────────────────────────────────

def run_comparison(queries: list = None):
    """Run all queries through all 3 frameworks and compare."""
    if queries is None:
        queries = TEST_QUERIES

    runners = {
        "LangChain": run_langchain,
        "LlamaIndex": run_llamaindex,
        "Pure SDK": run_pure_sdk,
    }

    results = {}

    for label, query in queries:
        print(f"\n{'='*60}")
        print(f"  {label}")
        print(f"  Query: {query}")
        print(f"{'='*60}")

        results[label] = {}
        for name, runner in runners.items():
            print(f"  [{name}] ", end="", flush=True)
            r = runner(query)
            results[label][name] = r
            if r["error"]:
                print(f"❌ Error: {r['error']}")
            else:
                print(f"✅ {r['time']}s")
            time.sleep(0.5)  # Rate limiting

    # ── Summary Table ──────────────────────────
    print(f"\n\n{'='*60}")
    print(f"  📊 COMPARISON SUMMARY")
    print(f"{'='*60}")

    # Header
    print(f"\n  {'Query':<25} {'Metric':<12} {'LangChain':<12} {'LlamaIndex':<12} {'Pure SDK':<12}")
    print(f"  {'-'*25} {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

    for label, data in results.items():
        times = []
        ok = []
        for name in ["LangChain", "LlamaIndex", "Pure SDK"]:
            r = data.get(name, {})
            times.append(str(r.get("time", "?")) + "s")
            ok.append("✅" if r.get("result") else "❌")

        print(f"  {label:<25} {'Time':<12} {times[0]:<12} {times[1]:<12} {times[2]:<12}")
        print(f"  {'':<25} {'Status':<12} {ok[0]:<12} {ok[1]:<12} {ok[2]:<12}")

    return results


# ──────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compare LangChain vs LlamaIndex vs Pure SDK")
    parser.add_argument("-q", "--query", type=str, help="Custom query to test")
    args = parser.parse_args()

    if args.query:
        run_comparison([("Custom", args.query)])
    else:
        run_comparison()

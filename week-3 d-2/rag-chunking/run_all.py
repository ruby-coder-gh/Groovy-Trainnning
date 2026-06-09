#!/usr/bin/env python3
"""
Run All — executes the full chunking evaluation pipeline end-to-end.

Pipeline:
  1. fetch_dataset.py   → Fetch OpenAI API docs (~5K-10K words)
  2. embed_store.py     → Chunk (4 strategies) → Embed → Store in ChromaDB
  3. evaluate.py        → For each of 10 queries, retrieve & score relevance
  4. reranker.py        → Compare vector search vs Cohere reranker precision

Usage:
    python run_all.py

Or run steps individually:
    python fetch_dataset.py
    python embed_store.py
    python evaluate.py
    python reranker.py
"""

import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).parent


def run_step(name: str, script: str) -> None:
    """Run a Python script and print status."""
    print(f"\n{'=' * 70}")
    print(f"  STEP: {name}")
    print(f"{'=' * 70}\n")

    start = time.time()
    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT_DIR,
        capture_output=False,
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        print(f"\n  ✅ {name} completed in {elapsed:.1f}s\n")
    else:
        print(f"\n  ❌ {name} FAILED (exit code {result.returncode})\n")
        sys.exit(result.returncode)


def main():
    print("=" * 70)
    print("  DAY 12 — CHUNKING + RETRIEVAL STRATEGIES")
    print("  Full Pipeline Execution")
    print("=" * 70)

    steps = [
        ("Fetch Dataset", "fetch_dataset.py"),
        ("Chunk → Embed → Store (4 strategies)", "embed_store.py"),
        ("Evaluate Retrieval Quality (10 queries)", "evaluate.py"),
        ("Cohere Reranker Comparison", "reranker.py"),
    ]

    for name, script in steps:
        script_path = ROOT_DIR / script
        if not script_path.exists():
            print(f"\n  ⚠ Script not found: {script_path}")
            continue
        run_step(name, str(script_path))

    print("=" * 70)
    print("  🎉 ALL STEPS COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()

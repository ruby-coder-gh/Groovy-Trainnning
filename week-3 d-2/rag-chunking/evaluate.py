#!/usr/bin/env python3
"""
Evaluation — measures retrieval quality across all 4 chunking strategies.

For each query (from queries.json):
  1. Embed the query using text-embedding-3-small
  2. Retrieve top-3 chunks from each strategy's ChromaDB collection
  3. Display retrieved chunks for manual scoring
  4. Generate a comparison table

Scoring:
  2 = Perfect (exactly what's needed to answer the query)
  1 = Partial (somewhat relevant, missing key details)
  0 = Wrong / Irrelevant
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

import chromadb
import cohere
from dotenv import load_dotenv

# Load .env but don't override real env vars with empty values
load_dotenv(override=False)

# ─── Configuration ────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
CHROMA_DIR = DATA_DIR / "chroma"
QUERIES_PATH = Path(__file__).parent / "queries.json"
RESULTS_PATH = Path(__file__).parent / "results.json"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embed-english-v3.0")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
TOP_K = 3

COLLECTION_NAMES = ["fixed", "sliding", "semantic", "hierarchical"]

# ─── Cohere Client ──────────────────────────────────────────

co = cohere.ClientV2(api_key=COHERE_API_KEY)

COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"
COLOR_BOLD = "\033[1m"
COLOR_MAGENTA = "\033[35m"


def get_embedding(text: str, input_type: str = "search_query") -> list[float]:
    """Get embedding vector using Cohere."""
    resp = co.embed(
        texts=[text],
        model=EMBEDDING_MODEL,
        input_type=input_type,
    )
    return resp.embeddings.float_[0]


def load_queries() -> list[dict]:
    """Load evaluation queries from JSON."""
    if not QUERIES_PATH.exists():
        print(f"✗ Queries file not found: {QUERIES_PATH}")
        sys.exit(1)
    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def retrieve(
    collection: Any,
    query_embedding: list[float],
    k: int = TOP_K,
) -> list[dict]:
    """Retrieve top-k chunks from a ChromaDB collection."""
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
    )

    items = []
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "score": (
                    1 - results["distances"][0][i]
                    if results.get("distances") and results["distances"][0]
                    else 0.0
                ),
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
            })
    return items


def display_retrieved(query: str, strategy: str, items: list[dict]) -> None:
    """Display retrieved chunks for visual inspection."""
    print(f"\n  {COLOR_BOLD}{COLOR_CYAN}Top-{len(items)} from '{strategy}':{COLOR_RESET}")
    for i, item in enumerate(items):
        relevance = item["score"]
        color = COLOR_GREEN if relevance > 0.7 else COLOR_YELLOW if relevance > 0.4 else COLOR_RED
        print(f"\n  {COLOR_BOLD}#{i + 1}{COLOR_RESET} (score: {color}{relevance:.4f}{COLOR_RESET})")
        # Show first 200 chars of the chunk
        preview = item["text"][:200].replace("\n", " | ")
        if len(item["text"]) > 200:
            preview += "..."
        print(f"    {preview}")


def prompt_score(query_id: str, strategy: str) -> int:
    """Prompt user to score the retrieval for a given query+strategy."""
    while True:
        try:
            score_str = input(
                f"\n  {COLOR_BOLD}Score for {COLOR_MAGENTA}{query_id}{COLOR_RESET}"
                f" ({COLOR_CYAN}{strategy}{COLOR_RESET})"
                f" [0=wrong, 1=partial, 2=perfect]: {COLOR_RESET}"
            )
            score = int(score_str.strip())
            if score in (0, 1, 2):
                return score
            print(f"  {COLOR_RED}Invalid score. Enter 0, 1, or 2.{COLOR_RESET}")
        except (ValueError, EOFError):
            print(f"  {COLOR_RED}Invalid input.{COLOR_RESET}")


def print_score_table(scores: dict[str, dict[str, int]]) -> None:
    """Print a formatted comparison table of scores."""
    print("\n" + "=" * 70)
    print(f"  {COLOR_BOLD}RETRIEVAL QUALITY SCORE TABLE{COLOR_RESET}")
    print("=" * 70)

    # Header
    print(f"\n  {'Query':<10}", end="")
    for s in COLLECTION_NAMES:
        print(f"  {s:<12}", end="")
    print()

    # Separator
    print(f"  {'-' * 10}", end="")
    for _ in COLLECTION_NAMES:
        print(f"  {'-' * 12}", end="")
    print()

    # Rows
    totals = {s: 0 for s in COLLECTION_NAMES}
    for q_id in sorted(scores.keys()):
        print(f"  {q_id:<10}", end="")
        for s in COLLECTION_NAMES:
            score = scores[q_id].get(s, 0)
            totals[s] += score
            color = COLOR_GREEN if score == 2 else COLOR_YELLOW if score == 1 else COLOR_RED
            print(f"  {color}{score:<12}{COLOR_RESET}", end="")
        print()

    # Totals row
    print(f"  {'-' * 10}", end="")
    for _ in COLLECTION_NAMES:
        print(f"  {'-' * 12}", end="")
    print()
    print(f"  {'TOTAL':<10}", end="")
    for s in COLLECTION_NAMES:
        color = COLOR_GREEN if totals[s] >= 15 else COLOR_YELLOW if totals[s] >= 10 else COLOR_RED
        print(f"  {color}{totals[s]:<12}{COLOR_RESET}", end="")
    print()

    # Average
    num_queries = len(scores)
    print(f"  {'AVG':<10}", end="")
    for s in COLLECTION_NAMES:
        avg = totals[s] / num_queries if num_queries > 0 else 0
        color = COLOR_GREEN if avg >= 1.5 else COLOR_YELLOW if avg >= 1.0 else COLOR_RED
        print(f"  {color}{avg:<12.2f}{COLOR_RESET}", end="")
    print()
    print("=" * 70)


def save_results(scores: dict, query_details: list[dict]) -> None:
    """Save results to a JSON file."""
    results = {
        "scores": scores,
        "query_details": query_details,
        "summary": {},
    }

    # Compute summary
    for s in COLLECTION_NAMES:
        strategy_scores = [scores[q["id"]].get(s, 0) for q in query_details]
        results["summary"][s] = {
            "total": sum(strategy_scores),
            "average": sum(strategy_scores) / len(strategy_scores) if strategy_scores else 0,
            "perfect": sum(1 for sc in strategy_scores if sc == 2),
            "partial": sum(1 for sc in strategy_scores if sc == 1),
            "wrong": sum(1 for sc in strategy_scores if sc == 0),
        }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n  📁 Results saved to {RESULTS_PATH}")


def main():
    print("=" * 70)
    print(f"  {COLOR_BOLD}RETRIEVAL QUALITY EVALUATION{COLOR_RESET}")
    print("=" * 70)

    # 1. Load queries
    print(f"\n{COLOR_BOLD}📋 Loading queries...{COLOR_RESET}")
    queries = load_queries()
    print(f"   {len(queries)} queries loaded")

    # 2. Initialize ChromaDB
    print(f"\n{COLOR_BOLD}🗄️  Connecting to ChromaDB...{COLOR_RESET}")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    print(f"   Path: {CHROMA_DIR}")

    # Verify collections exist
    existing = {c.name for c in chroma_client.list_collections()}
    for name in COLLECTION_NAMES:
        if name not in existing:
            print(f"   {COLOR_RED}✗ Collection '{name}' not found! Run embed_store.py first.{COLOR_RESET}")
            sys.exit(1)
        else:
            col = chroma_client.get_collection(name)
            print(f"   ✓ '{name}' ({col.count()} chunks)")

    # 3. Evaluate each query
    scores: dict[str, dict[str, int]] = {}
    query_details: list[dict] = []

    for q in queries:
        q_id = q["id"]
        q_text = q["query"]

        print(f"\n{'=' * 70}")
        print(f"  {COLOR_BOLD}{COLOR_MAGENTA}{q_id}:{COLOR_RESET} {q_text}")
        print(f"  Topic: {q['topic']}")
        print(f"{'=' * 70}")

        # Embed query
        print(f"\n  Embedding query...")
        query_embedding = get_embedding(q_text)

        # Retrieve from each strategy
        strategy_items = {}
        for strategy in COLLECTION_NAMES:
            collection = chroma_client.get_collection(strategy)
            items = retrieve(collection, query_embedding)
            strategy_items[strategy] = items
            display_retrieved(q_text, strategy, items)

        # Collect scores
        scores[q_id] = {}
        print(f"\n{COLOR_BOLD}{COLOR_YELLOW}━━━ Enter Scores ━━━{COLOR_RESET}")
        for strategy in COLLECTION_NAMES:
            s = prompt_score(q_id, strategy)
            scores[q_id][strategy] = s

        query_details.append({
            "id": q_id,
            "query": q_text,
            "topic": q["topic"],
            "scores": scores[q_id],
        })

    # 4. Print score table
    print_score_table(scores)

    # 5. Save results
    save_results(scores, query_details)

    # 6. Determine winner
    totals = {s: sum(scores[q].get(s, 0) for q in scores) for s in COLLECTION_NAMES}
    winner = max(totals, key=totals.get)
    print(f"\n{COLOR_BOLD}{COLOR_GREEN}🏆 Best strategy: {winner.upper()}"
          f" (total score: {totals[winner]}/{len(queries) * 2}){COLOR_RESET}")

    print(f"\n{COLOR_BOLD}Next step: Run `python reranker.py` to add Cohere reranking.{COLOR_RESET}\n")


if __name__ == "__main__":
    main()

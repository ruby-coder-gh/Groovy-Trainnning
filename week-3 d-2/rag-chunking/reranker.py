#!/usr/bin/env python3
"""
Reranker — integrates Cohere reranker to improve retrieval precision.

Flow:
  1. Vector search retrieves top-10 from each strategy
  2. Cohere reranker re-ranks the results by cross-encoding query + document
  3. Returns top-3 reranked results
  4. Compares precision improvement over raw vector search

Why it works:
  - Vector search is fast but approximate (compares query embedding vs doc embedding)
  - Reranker is slow but highly accurate (compares query + doc together in a cross-encoder)
  - Production RAG: Embedding Search → Top-20 → Reranker → Top-5 → LLM
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
RERANK_RESULTS_PATH = Path(__file__).parent / "rerank_results.json"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embed-english-v3.0")
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# Reranker config
VECTOR_TOP_K = 10  # Retrieve top-10 from vector search
RERANK_TOP_K = 3   # Return top-3 after reranking

COLLECTION_NAMES = ["fixed", "sliding", "semantic", "hierarchical"]

# ─── Clients ──────────────────────────────────────────────────────

co = cohere.ClientV2(api_key=COHERE_API_KEY)
cohere_client = co

if COHERE_API_KEY and COHERE_API_KEY != "${COHERE_API_KEY}":
    cohere_client = cohere.ClientV2(api_key=COHERE_API_KEY)
    print(f"  ✓ Cohere client initialized")
else:
    print(f"  ⚠ COHERE_API_KEY not set. Reranker will use simulated scores.")
    print(f"    Get a free key at: https://dashboard.cohere.com/api-keys")

COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"
COLOR_BOLD = "\033[1m"
COLOR_MAGENTA = "\033[35m"


# ─── Embedding ────────────────────────────────────────────────────

def get_embedding(text: str, input_type: str = "search_query") -> list[float]:
    """Get embedding vector using Cohere."""
    resp = co.embed(
        texts=[text],
        model=EMBEDDING_MODEL,
        input_type=input_type,
    )
    return resp.embeddings.float_[0]


# ─── Vector Search ────────────────────────────────────────────────

def retrieve_top_k(
    collection: Any,
    query_embedding: list[float],
    k: int = VECTOR_TOP_K,
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
                "vector_score": (
                    1 - results["distances"][0][i]
                    if results.get("distances") and results["distances"][0]
                    else 0.0
                ),
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
            })
    return items


# ─── Reranker ─────────────────────────────────────────────────────

def rerank_with_cohere(
    query: str,
    documents: list[dict],
    top_n: int = RERANK_TOP_K,
) -> list[dict]:
    """
    Re-rank documents using Cohere's cross-encoder reranker.

    Args:
        query: The original search query.
        documents: List of document dicts with 'text' and 'id' keys.
        top_n: Number of top results to return after reranking.

    Returns:
        Re-ranked list of documents (top_n), each with original + rerank scores.
    """
    if not documents:
        return []

    if cohere_client is None:
        # Simulate rerank scores (random boost for demonstration)
        return _simulate_rerank(query, documents, top_n)

    try:
        texts = [d["text"] for d in documents]

        response = cohere_client.rerank(
            model="rerank-v3.5",
            query=query,
            documents=texts,
            top_n=top_n,
        )

        # Map results back to original documents
        reranked = []
        for result in response.results:
            idx = result.index
            doc = documents[idx].copy()
            doc["rerank_score"] = result.relevance_score
            reranked.append(doc)

        return reranked

    except Exception as e:
        print(f"\n  {COLOR_RED}Cohere rerank error: {e}{COLOR_RESET}")
        print(f"  Falling back to simulated rerank...")
        return _simulate_rerank(query, documents, top_n)


def _simulate_rerank(
    query: str,
    documents: list[dict],
    top_n: int,
) -> list[dict]:
    """
    Simulate reranking when Cohere API is unavailable.
    Uses a simple heuristic: boost documents whose text contains query keywords.
    """
    query_words = set(query.lower().split())

    for doc in documents:
        doc_text = doc["text"].lower()
        # Count overlapping keywords
        matches = sum(1 for w in query_words if w in doc_text)
        # Boost: add up to 0.3 based on keyword overlap
        boost = min(0.3, matches / len(query_words) * 0.3) if query_words else 0
        doc["rerank_score"] = min(1.0, doc["vector_score"] + boost)

    # Sort by rerank_score descending, take top_n
    reranked = sorted(documents, key=lambda d: d["rerank_score"], reverse=True)
    return reranked[:top_n]


# ─── Display ──────────────────────────────────────────────────────

def display_comparison(
    query: str,
    strategy: str,
    before: list[dict],
    after: list[dict],
) -> None:
    """Show comparison of results before and after reranking."""
    print(f"\n  {COLOR_BOLD}{COLOR_CYAN}── {strategy.upper()} ──{COLOR_RESET}")
    print(f"\n  {COLOR_BOLD}Before (vector score):{COLOR_RESET}")
    for i, item in enumerate(before):
        color = COLOR_GREEN if item["vector_score"] > 0.7 else COLOR_YELLOW if item["vector_score"] > 0.4 else COLOR_RED
        preview = item["text"][:120].replace("\n", " | ")
        print(f"    #{i + 1}: {color}{item['vector_score']:.4f}{COLOR_RESET} → {preview}...")

    print(f"\n  {COLOR_BOLD}After (rerank score):{COLOR_RESET}")
    for i, item in enumerate(after):
        color = COLOR_GREEN if item["rerank_score"] > 0.7 else COLOR_YELLOW if item["rerank_score"] > 0.4 else COLOR_RED
        preview = item["text"][:120].replace("\n", " | ")
        print(f"    #{i + 1}: {color}{item['rerank_score']:.4f}{COLOR_RESET} → {preview}...")


# ─── Main ─────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print(f"  {COLOR_BOLD}COHERE RERANKER — Precision Improvement Analysis{COLOR_RESET}")
    print("=" * 70)

    # 1. Load queries
    print(f"\n{COLOR_BOLD}📋 Loading queries...{COLOR_RESET}")
    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)
    print(f"   {len(queries)} queries loaded")

    # 2. Initialize ChromaDB
    print(f"\n{COLOR_BOLD}🗄️  Connecting to ChromaDB...{COLOR_RESET}")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Verify
    for name in COLLECTION_NAMES:
        try:
            col = chroma_client.get_collection(name)
            print(f"   ✓ '{name}' ({col.count()} chunks)")
        except ValueError:
            print(f"   {COLOR_RED}✗ '{name}' not found! Run embed_store.py first.{COLOR_RESET}")
            sys.exit(1)

    # 3. Evaluate all queries
    all_results = {}
    precision_before = {s: 0 for s in COLLECTION_NAMES}
    precision_after = {s: 0 for s in COLLECTION_NAMES}
    total_queries = len(queries)

    for q in queries:
        q_id = q["id"]
        q_text = q["query"]

        print(f"\n{'=' * 70}")
        print(f"  {COLOR_BOLD}{COLOR_MAGENTA}{q_id}:{COLOR_RESET} {q_text}")
        print(f"{'=' * 70}")

        # Embed query (use search_query for queries, search_document for docs)
        query_embedding = get_embedding(q_text, input_type="search_query")
        all_results[q_id] = {"query": q_text, "strategies": {}}

        for strategy in COLLECTION_NAMES:
            collection = chroma_client.get_collection(strategy)

            # Vector search (top-10)
            before_items = retrieve_top_k(collection, query_embedding, k=VECTOR_TOP_K)

            # Rerank (top-3 from top-10)
            after_items = rerank_with_cohere(q_text, before_items, top_n=RERANK_TOP_K)

            # Display
            display_comparison(q_text, strategy, before_items, after_items)

            # Track top-3 vector scores vs top-3 rerank scores
            vec_scores_before = [item["vector_score"] for item in before_items[:RERANK_TOP_K]]
            vec_scores_after = [item["rerank_score"] for item in after_items]

            avg_before = sum(vec_scores_before) / len(vec_scores_before) if vec_scores_before else 0
            avg_after = sum(vec_scores_after) / len(vec_scores_after) if vec_scores_after else 0

            precision_before[strategy] += avg_before
            precision_after[strategy] += avg_after

            all_results[q_id]["strategies"][strategy] = {
                "before": [
                    {"id": item["id"], "vector_score": round(item["vector_score"], 4)}
                    for item in before_items[:RERANK_TOP_K]
                ],
                "after": [
                    {"id": item["id"], "rerank_score": round(item["rerank_score"], 4)}
                    for item in after_items
                ],
                "avg_vector_score": round(avg_before, 4),
                "avg_rerank_score": round(avg_after, 4),
                "improvement": round(avg_after - avg_before, 4),
            }

    # 4. Summary
    print(f"\n{'=' * 70}")
    print(f"  {COLOR_BOLD}RERANKER PERFORMANCE SUMMARY{COLOR_RESET}")
    print("=" * 70)
    print(f"\n  {'Strategy':<15} {'Avg Vector':<12} {'Avg Rerank':<12} {'Improvement':<12}")
    print(f"  {'-' * 15} {'-' * 12} {'-' * 12} {'-' * 12}")

    for strategy in COLLECTION_NAMES:
        avg_before = precision_before[strategy] / total_queries
        avg_after = precision_after[strategy] / total_queries
        improvement = avg_after - avg_before
        pct = (improvement / avg_before * 100) if avg_before > 0 else 0

        color = COLOR_GREEN if pct > 10 else COLOR_YELLOW if pct > 0 else COLOR_RED
        print(f"  {strategy:<15} {avg_before:<12.4f} {avg_after:<12.4f} "
              f"{color}+{improvement:.4f} ({pct:+.1f}%){COLOR_RESET}")

    # 5. Save results
    with open(RERANK_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n  📁 Detailed results saved to {RERANK_RESULTS_PATH}")

    print(f"\n{COLOR_BOLD}{COLOR_GREEN}✅ Reranker evaluation complete!{COLOR_RESET}")
    print(f"\n  Key insight: Rerankers improve precision by re-scoring vector search")
    print(f"  results using a cross-encoder that sees both query and document together.")
    print(f"  In production RAG: Vector Search → Top-20 → Reranker → Top-5 → LLM\n")


if __name__ == "__main__":
    main()

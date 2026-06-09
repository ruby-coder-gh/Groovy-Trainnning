#!/usr/bin/env python3
"""
Embed & Store — generates embeddings and stores in ChromaDB collections.

Creates 4 separate collections:
  - collection_fixed
  - collection_sliding
  - collection_semantic
  - collection_hierarchical

Uses the same embedding model (text-embedding-3-small) for fairness.
"""

import os
import json
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import chromadb
import cohere
from dotenv import load_dotenv

from chunkers import FixedChunker, SlidingWindowChunker, SemanticChunker, HierarchicalChunker

# Load .env but don't override real env vars with empty values
load_dotenv(override=False)

# ─── Configuration ────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent / "data"
CHROMA_DIR = DATA_DIR / "chroma"
DOCUMENT_PATH = DATA_DIR / "raw.txt"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "embed-english-v3.0")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "1024"))
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")

# Chunking config — larger chunks = fewer chunks = faster
FIXED_CHUNK_SIZE = 1000
SLIDING_CHUNK_SIZE = 1000
SLIDING_OVERLAP = 200
SEMANTIC_CHUNK_SIZE = 1000
SEMANTIC_OVERLAP = 100
HIERARCHICAL_MAX_PARAGRAPH = 1000

# ─── Cohere Client ──────────────────────────────────────────

co = cohere.ClientV2(api_key=COHERE_API_KEY)

COLLECTION_NAMES = ["fixed", "sliding", "semantic", "hierarchical"]

# Cohere embedding parameters
INPUT_TYPE_QUERY = "search_query"
INPUT_TYPE_DOC = "search_document"


def _embed_single(text: str) -> list[float]:
    """Embed a single text string using Cohere."""
    resp = co.embed(
        texts=[text],
        model=EMBEDDING_MODEL,
        input_type=INPUT_TYPE_DOC,
    )
    return resp.embeddings.float_[0]


def get_embedding(text: str) -> list[float]:
    """Get embedding vector for a single text string."""
    return _embed_single(text)


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings in parallel — Cohere handles batching internally."""
    all_embeddings = []
    total = len(texts)
    batch_size = 10  # Cohere batch size
    
    for start in range(0, total, batch_size):
        batch = texts[start:start + batch_size]
        resp = co.embed(
            texts=batch,
            model=EMBEDDING_MODEL,
            input_type=INPUT_TYPE_DOC,
        )
        all_embeddings.extend(resp.embeddings.float_)
        done = min(start + batch_size, total)
        print(f"    ✓ {done}/{total}", end="\r")
    
    print(f"\n    ✅ Embedded {total} texts")
    return all_embeddings


def load_document() -> str:
    """Load the test document from disk."""
    if not DOCUMENT_PATH.exists():
        raise FileNotFoundError(
            f"Document not found at {DOCUMENT_PATH}. "
            "Run `python fetch_dataset.py` first."
        )
    return DOCUMENT_PATH.read_text(encoding="utf-8")


def create_chroma_collection(
    client: chromadb.Client,
    name: str,
) -> Any:
    """Create or recreate a ChromaDB collection."""
    try:
        client.delete_collection(name)
        print(f"    Deleted existing collection '{name}'")
    except Exception:
        pass  # Collection doesn't exist yet

    collection = client.create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def add_chunks_to_collection(
    collection: Any,
    chunks: list[dict],
    strategy: str,
) -> None:
    """
    Embed chunks and add them to a ChromaDB collection.

    Args:
        collection: ChromaDB collection object.
        chunks: List of chunk dicts with 'text' key.
        strategy: Strategy name for metadata.
    """
    if not chunks:
        print(f"    ⚠ No chunks to add!")
        return

    texts = [c["text"] for c in chunks]
    print(f"    Generating {len(texts)} embeddings...")
    embeddings = get_embeddings_batch(texts)

    ids = [f"{strategy}_{c['index']}" for c in chunks]
    metadatas = []
    for c in chunks:
        meta = {
            "strategy": strategy,
            "index": c["index"],
            "char_start": c.get("char_start", 0),
            "char_end": c.get("char_end", 0),
        }
        # Add hierarchical metadata if present
        if "section_heading" in c:
            meta["section_heading"] = c["section_heading"]
            meta["section_index"] = c["section_index"]
            meta["level"] = c["level"]
            meta["paragraph_index"] = c["paragraph_index"]
        metadatas.append(meta)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"    ✅ Added {len(chunks)} chunks to '{collection.name}'")


def process_strategy(
    chroma_client: chromadb.Client,
    strategy_name: str,
    text: str,
) -> tuple[Any, list[dict]]:
    """
    Run a chunking strategy and store results in ChromaDB.

    Args:
        chroma_client: ChromaDB client.
        strategy_name: One of 'fixed', 'sliding', 'semantic', 'hierarchical'.
        text: The full document text.

    Returns:
        (collection, chunks) tuple.
    """
    print(f"\n  ── {strategy_name.upper()} ──")

    # 1. Create collection
    collection = create_chroma_collection(chroma_client, strategy_name)

    # 2. Chunk
    if strategy_name == "fixed":
        chunker = FixedChunker(chunk_size=FIXED_CHUNK_SIZE)
    elif strategy_name == "sliding":
        chunker = SlidingWindowChunker(
            chunk_size=SLIDING_CHUNK_SIZE, overlap=SLIDING_OVERLAP
        )
    elif strategy_name == "semantic":
        chunker = SemanticChunker(
            chunk_size=SEMANTIC_CHUNK_SIZE, overlap=SEMANTIC_OVERLAP
        )
    elif strategy_name == "hierarchical":
        chunker = HierarchicalChunker(
            max_paragraph_chars=HIERARCHICAL_MAX_PARAGRAPH
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    chunks = chunker.chunk(text)
    print(f"    Generated {len(chunks)} chunks")

    # 3. Embed + store
    add_chunks_to_collection(collection, chunks, strategy_name)

    return collection, chunks


def save_strategy_metadata(strategy: str, chunks: list[dict]) -> None:
    """Save chunk metadata to a JSON file for later analysis."""
    meta_dir = DATA_DIR / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)

    # Strip text content to keep file size reasonable (keep first 100 chars as preview)
    meta_chunks = []
    for c in chunks:
        mc = {k: v for k, v in c.items() if k != "text"}
        mc["text_preview"] = c["text"][:100] + "..." if len(c["text"]) > 100 else c["text"]
        mc["text_length"] = len(c["text"])
        meta_chunks.append(mc)

    output_path = meta_dir / f"{strategy}_chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "strategy": strategy,
                "total_chunks": len(chunks),
                "chunks": meta_chunks,
            },
            f,
            indent=2,
        )
    print(f"    📁 Metadata saved to {output_path}")


def print_summary(results: dict[str, tuple[Any, list[dict]]]) -> None:
    """Print a summary of all strategies."""
    print("\n" + "=" * 60)
    print("  STRATEGY SUMMARY")
    print("=" * 60)

    for name, (_, chunks) in results.items():
        avg_len = sum(len(c["text"]) for c in chunks) / len(chunks) if chunks else 0
        print(f"\n  {name.upper():15s} | {len(chunks):4d} chunks | avg {avg_len:.0f} chars")

    print("\n" + "=" * 60)


def main():
    print("=" * 60)
    print("  Embed & Store — ChromaDB Collections")
    print("=" * 60)

    # 1. Load document
    print("\n📄 Loading document...")
    text = load_document()
    word_count = len(text.split())
    print(f"   {word_count:,} words, {len(text):,} characters")

    # 2. Initialize ChromaDB
    print("\n🗄️  Initializing ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    print(f"   Path: {CHROMA_DIR}")

    # 3. Process each strategy
    results = {}
    for strategy in COLLECTION_NAMES:
        collection, chunks = process_strategy(chroma_client, strategy, text)
        results[strategy] = (collection, chunks)
        save_strategy_metadata(strategy, chunks)

    # 4. Summary
    print_summary(results)

    # 5. Verify
    print("\n🔍 Verifying collections...")
    for name in COLLECTION_NAMES:
        col = chroma_client.get_collection(name)
        count = col.count()
        print(f"   {name:15s}: {count} chunks")

    print("\n✅ All done! ChromaDB collections ready for evaluation.")
    print(f"   Run `python evaluate.py` to test retrieval quality.\n")


if __name__ == "__main__":
    main()

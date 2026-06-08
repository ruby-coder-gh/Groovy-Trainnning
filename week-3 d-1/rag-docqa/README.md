# RAG Doc-Q&A v2 — Day 11

**Retrieval-Augmented Generation meets Document Q&A**

RAG-powered document Q&A system that extracts text from PDFs, chunks it intelligently, generates embeddings via OpenAI, stores them in a vector database (ChromaDB with JSON fallback), and answers questions by retrieving only the most relevant chunks — **not** the entire document.

---

## Table of Contents

- [Architecture](#architecture)
- [The Theory](#the-theory)
  - [What Are Embeddings?](#what-are-embeddings)
  - [Cosine Similarity](#cosine-similarity)
  - [Vector Databases](#vector-databases)
  - [RAG vs Full-Doc](#rag-vs-full-doc)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage: CLI](#usage-cli)
  - [Ingest a Document](#1-ingest-a-document)
  - [Query the Document](#2-query-the-document)
  - [Interactive Chat Mode](#3-interactive-chat-mode)
- [Usage: API Server](#usage-api-server)
  - [Upload & Ask via curl](#upload--ask-via-curl)
- [Cost Comparison](#cost-comparison)
- [Extending the System](#extending-the-system)
- [How Each Module Works](#how-each-module-works)

---

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │         RAG Doc-Q&A v2              │
                    │                                     │
  PDF ──► lib/pdfParser.js ──► lib/chunker.js             │
                                      │                   │
                                      ▼                   │
                              lib/embedder.js             │
                              (OpenAI text-embedding-3-small)
                                      │                   │
                                      ▼                   │
                              lib/vectordb.js             │
                              (ChromaDB / JSON fallback)  │
                                      │                   │
  Question ──► lib/embedder.js        │                   │
                  │                   │                   │
                  ▼                   ▼                   │
           cosineSimilarity()  ◄── Query top-3            │
                  │                                       │
                  ▼                                       │
           Top-3 chunks + question ──► LLM (OpenAI /     │
                                       Anthropic / Ollama)│
                  │                                       │
                  ▼                                       │
           Answer with citations ───────► User            │
                    └─────────────────────────────────────┘
```

### Data Flow

1. **Ingest**: PDF → parse text → chunk (with overlap) → embed each chunk → store vectors in ChromaDB
2. **Query**: Question → embed → cosine similarity search in vector DB → retrieve top-3 chunks → build context with citations → send to LLM → return answer with source pages

---

## The Theory

### What Are Embeddings?

An **embedding** is a dense vector (array of floats) that captures the **semantic meaning** of a piece of text. OpenAI's `text-embedding-3-small` produces 1536-dimensional vectors.

Key properties:
- **Semantic proximity**: Similar meanings produce similar vectors
- **Fixed dimension**: Every text fragment maps to the same vector length
- **Dense**: Unlike one-hot encoding, every dimension carries information

Example (simplified to 4 dimensions):
```
"king"    → [0.92, 0.31, -0.45, 0.78]
"queen"   → [0.88, 0.28, -0.42, 0.82]  ← very similar to "king"
"apple"   → [0.12, 0.95,  0.33, 0.11]  ← very different from "king"
```

### Cosine Similarity

The standard way to compare two embeddings:

```
cos(θ) = (A · B) / (‖A‖ · ‖B‖)
```

Where:
- `A · B` is the dot product of vectors A and B
- `‖A‖` is the magnitude (length) of vector A
- `‖B‖` is the magnitude (length) of vector B

**Range**: [-1, 1]
- **1.0**: Identical direction (same meaning)
- **0.0**: Orthogonal (no relationship)
- **-1.0**: Opposite direction (opposite meaning)

**Why cosine?** It measures **direction**, not magnitude. "Running" and "run" should be similar even though one is longer — their directions in vector space are close.

See `examples/cosine-similarity.js` for an interactive demo.

### Vector Databases

A vector database stores embeddings and supports **similarity search** (ANN — Approximate Nearest Neighbor).

We support two backends:

| Feature | ChromaDB | JSON Fallback |
|---------|----------|---------------|
| Algorithm | HNSW (Hierarchical Navigable Small World) | Brute-force cosine similarity |
| Speed | O(log n) | O(n) |
| Persistence | On disk via SQLite/HNSW | JSON file |
| Dependencies | `chromadb` npm package | None (pure JS) |

ChromaDB is used when available. The JSON fallback activates automatically when ChromaDB is not installed.

### RAG vs Full-Doc

| Aspect | Full-Doc (v1) | RAG (v2) |
|--------|---------------|----------|
| **Tokens per query** | Entire document (~50K) | Only top-3 chunks (~1.5K) |
| **Cost per query** | ~$0.0075 (gpt-4o-mini) | ~$0.000225 (gpt-4o-mini) |
| **Accuracy** | Higher (has all context) | Depends on retrieval quality |
| **Context window** | Model limit (128K max) | Always fits (1.5K chunks) |
| **Supports 1000-page docs** | No (context window overflow) | Yes (any length) |
| **One-time embedding cost** | $0 | ~$0.001 per 100 pages |

**RAG wins on cost and scalability. Full-doc wins on simplicity and baseline accuracy.**

---

## Project Structure

```
week-3 d-1/rag-docqa/
├── ingest.js                    # CLI: PDF → chunks → embeddings → store
├── query.js                     # CLI: question → retrieve → LLM → answer
├── server.js                    # Express API server
├── package.json
├── .env.example
├── README.md
│
├── lib/
│   ├── chunker.js               # Recursive text chunking with overlap
│   ├── embedder.js              # OpenAI embedding wrapper + cosine similarity
│   ├── vectordb.js              # ChromaDB client with JSON fallback
│   └── pdfParser.js             # PDF text extraction (pdfjs-dist)
│
├── examples/
│   └── cosine-similarity.js     # Interactive similarity demo
│
├── meetup/
│   └── week-2-retro.md          # Week 2 retrospective
│
├── data/
│   ├── docs/                    # Place PDFs here for CLI ingest
│   │   └── .gitkeep
│   ├── chroma/                  # ChromaDB persistence directory
│   │   └── .gitkeep
│   └── telemetry.csv            # Generated telemetry log
│
└── uploads/                     # Server uploads (temporary)
```

---

## Setup

### Prerequisites
- Node.js 18+ (for global `fetch`)
- An OpenAI API key (for embeddings)
- (Optional) Ollama running locally for free LLM queries

### Install

```bash
cd "week-3 d-1/rag-docqa"
cp .env.example .env
# Edit .env with your API keys
npm install
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | OpenAI API key (required for embeddings) |
| `ANTHROPIC_API_KEY` | — | Anthropic API key (for Claude) |
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, or `ollama` |
| `LLM_MODEL` | `gpt-4o-mini` | Model name for the LLM provider |
| `CHUNK_SIZE` | `500` | Target tokens per chunk |
| `CHUNK_OVERLAP` | `50` | Overlap tokens between chunks |
| `TOP_K` | `3` | Number of chunks to retrieve per query |
| `PORT` | `3001` | Express server port |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `qwen3:8b` | Ollama model |

---

## Usage: CLI

### 1. Ingest a Document

```bash
# Basic usage
node ingest.js data/docs/sample.pdf

# With custom chunk size
CHUNK_SIZE=300 node ingest.js data/docs/sample.pdf
```

**What happens:** Parse → chunk into 500-token segments (50-token overlap) → embed each chunk via OpenAI → store 1536-d vectors in ChromaDB.

**Output:**
```
╔══════════════════════════════════════════════╗
║   Ingest Pipeline — Day 11                   ║
╚══════════════════════════════════════════════╝

📄 Parsing PDF: data/docs/sample.pdf
   Pages: 12
   Total tokens: ~4,800

✂️  Chunking...
   Chunks created: 12
   Avg tokens/chunk: 410

🧠 Generating embeddings (12 chunks)...
   Batch size: 12, tokens: 4,800
   Embeddings cost: $0.000096 (text-embedding-3-small)

💾 Storing in vector DB...
   Using ChromaDB backend
   Store count after ingest: 12
   Ingest time: 2.3s
```

### 2. Query the Document

```bash
# Basic query
node query.js "What is this document about?"

# Specify top-K
node query.js --top-k 5 "Explain the architecture"

# Use a different LLM provider
LLM_PROVIDER=anthropic LLM_MODEL=claude-sonnet-4-20250514 node query.js "Summarize the key points"
```

**Output:**
```
🔍 RAG Query Pipeline — Day 11
   Question: What is this document about?
   Top-K:    3
   LLM:      openai (gpt-4o-mini)

🧠 Step 1: Embedding question...
   Done (1536 dimensions)

📂 Step 2: Retrieving top 3 chunks...
   Found 3 relevant chunks

  ── Retrieved Chunks ──

  [Chunk 00005] (Page 3, similarity: 89.2%)
  The system architecture uses a microservices pattern...

  [Chunk 00008] (Page 5, similarity: 76.1%)
  Authentication is handled via JWT tokens...

  [Chunk 00002] (Page 2, similarity: 62.3%)
  This document describes the API specification...

🤖 Step 3: Generating answer (openai)...

This document describes a microservices-based API system.
The architecture uses JWT authentication [Page 5] and follows
a microservices pattern [Page 3]. Key components include...

  ───────────────────────────────────────────────
  Query tokens:     45
  Context tokens:   1,420 (3 chunks)
  Response tokens:  187
  Cost:             $0.000225
  ───────────────────────────────────────────────
  💰 RAG Savings vs Full-Doc:   97.0%
     Full-doc cost:  $0.007500
     RAG cost:       $0.000225
```

### 3. Interactive Chat Mode

```bash
node query.js --interactive

💬 RAG Chat Mode — type your questions (or 'exit')

Q: What is this document about?
Q: Explain the authentication flow
Q: exit
```

---

## Usage: API Server

```bash
node server.js

╔══════════════════════════════════════════════╗
║   RAG Doc-Q&A v2 — Server (Day 11)          ║
║   Listening on http://localhost:3001        ║
║   Endpoints:                                 ║
║     POST /api/upload   — Upload PDF + Ingest ║
║     POST /api/ask      — RAG Question Answer ║
║     GET  /api/cost     — Cost + Comparison   ║
║     GET  /api/health   — Health check        ║
║                                               ║
║   Vector store: 12 chunks ready              ║
╚══════════════════════════════════════════════╝
```

### Upload & Ask via curl

```bash
# Upload a PDF
curl -X POST http://localhost:3001/api/upload \
  -F "pdf=@data/docs/sample.pdf"

# Ask a question (after uploading)
curl -X POST http://localhost:3001/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'

# Response:
{
  "answer": "This document describes... [Page 1]",
  "citations": [
    { "page": 1, "excerpt": "The system architecture...", "similarity": 0.89 },
    { "page": 3, "excerpt": "Authentication is handled...", "similarity": 0.76 }
  ],
  "cost": {
    "model": "gpt-4o-mini",
    "inputTokens": 1465,
    "outputTokens": 187,
    "queryCost": 0.000225,
    "fullDocCost": 0.0075,
    "savings": "97.0%"
  }
}

# Get cost telemetry
curl http://localhost:3001/api/cost
```

---

## Cost Comparison

### Per-Query Costs (gpt-4o-mini, $0.15/1M input, $0.60/1M output)

| Document Size | Full-Doc Tokens | Full-Doc Cost | RAG Tokens (top-3) | RAG Cost | Savings |
|--------------|----------------|---------------|-------------------|----------|---------|
| 10 pages (~4K tok) | 4,000 | $0.000600 | 1,500 | $0.000225 | 62.5% |
| 50 pages (~20K tok) | 20,000 | $0.003000 | 1,500 | $0.000225 | 92.5% |
| 200 pages (~80K tok) | 80,000 | $0.012000 | 1,500 | $0.000225 | **98.1%** |
| 500 pages (~200K tok) | ❌ Exceeds context window | — | 1,500 | $0.000225 | ∞ |

### One-Time Embedding Cost

| Pages | Chunks (500-tok) | Tokens | Embedding Cost (text-embedding-3-small, $0.02/1M) |
|-------|-----------------|--------|--------------------------------------------------|
| 10 | ~10 | ~4,000 | $0.00008 |
| 100 | ~100 | ~40,000 | $0.00080 |
| 1,000 | ~1,000 | ~400,000 | $0.00800 |

**The embedding cost pays for itself after ~3 queries on a 100-page document.**

### 10,000 Query Projection

| Approach | Embedding Cost | Per-Query Cost | Total (10K queries) |
|----------|---------------|----------------|-------------------|
| Full-Doc (50 pages) | $0 | $0.003 | **$30.00** |
| RAG (50 pages) | $0.0008 | $0.000225 | **$2.25 + $0.0008 = $2.2508** |
| **Savings** | | | **$27.75 (92.5%)** |

---

## How Each Module Works

### `lib/chunker.js` — Recursive Character Splitting

Chunks text using a recursive strategy:

1. **Try paragraph breaks** (`\n\n`) within the chunk window
2. **Fall back to sentence breaks** (`.!?` followed by space)
3. **Fall back to word breaks** (last space within window)
4. **Hard cut** at `chunkSize` characters if none of the above

Each chunk carries its `pageNumber`, `source` page range, and `index` for provenance.

### `lib/embedder.js` — OpenAI Embedding Wrapper

- Uses `text-embedding-3-small` (1536 dimensions, $0.02/1M tokens)
- `embed(text)`: single text → vector
- `embedBatch(texts)`: array of texts → array of vectors (batched)
- `cosineSimilarity(a, b)`: pure-JS cosine similarity (no deps)
- `estimateCost(texts)`: token + cost estimator

### `lib/vectordb.js` — ChromaDB + JSON Fallback

**ChromaDB mode:** Creates a `hnsw:space=cosine` collection, adds items with `pageNumber` and `source` metadata, queries with `nResults`.

**JSON fallback:** Stores vectors + metadata in a JSON file, performs brute-force cosine similarity search on query. Activated when ChromaDB's `PageReader` can't find its native modules.

### `lib/pdfParser.js` — PDF Text Extraction

Wraps `pdfjs-dist` to extract text per page. Returns `{ pages: [{ pageNumber, text }], totalPages, fullText }`.

### `ingest.js` — Orchestration Pipeline

1. Parse PDF → get pages array
2. Chunk pages → array of { text, pageNumber, metadata }
3. Embed all chunks in batches → array of vectors
4. Clear existing vectors in store
5. Add all items (text + embedding + metadata)
6. Save ingest metadata for cost comparison

### `query.js` — Retrieval + Answering

1. Embed the user's question → query vector
2. Search vector DB for top-k most similar chunks
3. Build LLM context from chunks (with page citations)
4. Call LLM provider (OpenAI / Anthropic / Ollama)
5. Parse and display answer + cost + savings comparison

### `server.js` — Express API

Three endpoints wrapping the ingest + query pipeline with streaming response for upload progress.

---

## Extending the System

### Add a New LLM Provider

In `query.js` (and `server.js`), add a new `callXxx()` function:

```javascript
async function callCustomLLM(userPrompt) {
  // Call your provider's API
  return { text, inputTokens, outputTokens, cost };
}
```

Then add the provider to the `if/else` chain in `answerWithLLM()`.

### Switch Vector Database

Replace `lib/vectordb.js` with a client for Pinecone, Weaviate, Qdrant, or pgvector. Maintain the same interface:

```javascript
module.exports = {
  init: async () => { /* connect */ },
  addItems: async (items) => { /* upsert vectors */ },
  query: async (vector, k) => { /* search */ },
  count: async () => { /* return size */ },
  clear: async () => { /* delete all */ },
};
```

### Add Reranking

After retrieving top-k from vector DB, pass chunks through a cross-encoder (e.g., Cohere rerank or BAAI/bge-reranker) to reorder by relevance:

```
retrieved = vectordb.query(vector, 10)    // Get top-10
reranked = crossEncoder.rerank(question, retrieved)  // Re-rank
top3 = reranked.slice(0, 3)               // Pick top-3 after reranking
```

### Add Hybrid Search (BM25 + Vector)

```javascript
const bm25Results = bm25Search(question, allChunks);  // Keyword matches
const vectorResults = await vectordb.query(vector, 5); // Semantic matches

// Reciprocal Rank Fusion (RRF)
const fused = rrf(bm25Results, vectorResults);
const top3 = fused.slice(0, 3);
```

---

## Related

- **Week 2 Day 5** (`week-2 d-5/smart-doc-qa/`): The original full-doc Q&A system this was built on
- **Week 2 Day 4** (`week-2 d-4/telemetry/`): Telemetry CSV logger used across both versions
- **Week 3 Day 12**: Reranking (cross-encoder)
- **Week 3 Day 13**: Hybrid search (BM25 + vector)
- **Week 3 Day 15**: Evaluation (hit rate, MRR metrics)

# Week 2 Retrospective

**Team:** Groovy Training  
**Project:** Smart Doc Q&A → RAG Doc-Q&A v2  
**Date:** Week 2 → Day 11 Transition

---

## ✅ What Worked

### 1. Prompt Caching (Day 9 / W2D4)
System prompts are now cached and reused — huge latency savings when the system instruction doesn't change between queries.

### 2. Incremental Architecture
Building from CLI → Express → React client over the week created clean separation. The CLI was invaluable for debugging the core pipeline before wrapping it in an API.

### 3. Telemetry from Day 1
The CSV telemetry logger paid off big. Every API call (provider, model, tokens, cost, latency) was tracked since Day 9. We had real numbers for the cost comparison table.

### 4. Ollama for Local Testing
Running `qwen3:8b` locally via Ollama meant zero API cost during development. We only needed API keys for the final cost benchmark.

### 5. PDF Parsing
`pdfjs-dist` handled everything we threw at it — multi-column layouts, embedded images, scanned pages (with varying success). Page-number extraction was straightforward.

---

## 🧠 What Was Hard

### 1. Token Estimation Without a Tokenizer
We didn't have access to OpenAI's `tiktoken` tokenizer in the chunker. We used `Math.ceil(text.length / 4)` as an approximation. It's ~75% accurate for English text, but code/numeric content is off by 2-3x.

**Lesson:** Bundle `tiktoken` or the `gpt-tokenizer` npm package for production use.

### 2. ChromaDB Setup
ChromaDB's Node.js client (`chromadb`) requires `fetch` to be globally available (Node 18+). The HNSW index configuration (`hnsw:space=cosine`) needed explicit parameter docs — not obvious from the API reference.

**Lesson:** With the JSON fallback in place, we verified correctness first, then swapped to ChromaDB for production.

### 3. Chunk Boundary Awareness
Initial chunking split in the middle of sentences and paragraphs. We had to add recursive splitting rules: prefer paragraph breaks > sentence breaks > word breaks. This added ~60 lines of logic but dramatically improved retrieval quality.

### 4. Cost Comparison Honesty
RAG appears dramatically cheaper (95%+ savings), but the comparison isn't perfectly fair:
- RAG cost **includes** embedding generation (one-time, amortized)
- Full-doc cost **omits** the "store full text in memory" step (free)
- Embedding costs are upfront; retrieval costs are per-query

We chose to present the **per-query** comparison only, which is the most honest comparison.

---

## 🚀 Next Goals

### Week 3 (Days 11–15): Production RAG System

| Day | Goal |
|-----|------|
| **11** | ✅ RAG pipeline: chunking + embeddings + vector DB + retrieval |
| **12** | Reranking: improve retrieval with cross-encoder reranker |
| **13** | Hybrid search: BM25 keyword + vector search fusion |
| **14** | Chat history: multi-turn conversations with RAG |
| **15** | Evaluation: synthetic QA dataset, metrics (hit rate, MRR) |

### Stretch Goals
- Streaming responses from the LLM via SSE
- Web UI with drag-and-drop PDF + chat interface
- Support for non-PDF documents (DOCX, Markdown, plain text)

---

## 💰 Cost Reality Check

| Approach | Per-Query Tokens | Per-Query Cost | 10K Queries |
|----------|-----------------|----------------|-------------|
| Full-Doc (v1) | ~50,000 | ~$0.0075 | ~$75.00 |
| RAG (v2) | ~1,500 | ~$0.000225 | ~$2.25 |
| **Savings** | **97%** | **97%** | **$72.75** |

*Based on gpt-4o-mini pricing ($0.15/1M input, $0.60/1M output)*

The RAG approach pays for its infrastructure cost (embeddings: ~$0.001 per 100 pages, ChromaDB: $0) within the first ~15 queries.

---

*"Week 2 taught us how to talk to documents. Week 3 will teach us how to search them."*

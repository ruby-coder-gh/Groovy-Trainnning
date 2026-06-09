# 🧩 Chunking + Retrieval Strategies

**Yo, welcome!** This is my Day 12 deep dive into RAG (Retrieval-Augmented Generation) — where I took a big ol' document, chopped it up four different ways, stuffed it into ChromaDB, and then poked and prodded it to see what works best.

## 🎯 The Mission

Simple question: **Does *how* you chunk a document actually matter when you're trying to find stuff in it?**

Turns out — YES. Big time.

I took the OpenAI API documentation (~5,200 words), split it using 4 different chunking strategies, embedded everything with Cohere, stored it in ChromaDB, wrote 10 realistic queries, and evaluated how well each strategy retrieved relevant chunks. Then I threw a Cohere reranker on top just to see if things got even better.

## 🗺️ The 4 Chunking Strategies (and the vibes)

### 1️⃣ Fixed-Size Chunking (`fixed.py`)
> **"Just cut it every 1000 characters, idc"**

The no-frills approach. Hard cut at 1000 chars, zero overlap, no thinking required. It's fast, it's simple, and sometimes it cuts a sentence right in half like a bad haircut.

```
📄 → [──── 1000 chars ────] [──── 1000 chars ────] [──── 1000 chars ────]
```

**Chunks produced:** 35 (avg 994 chars each)

### 2️⃣ Sliding Window (`sliding.py`)
> **"Let me overlap a bit so I don't lose the plot"**

Same fixed-size chunks, but with 200 characters of overlap between them. Now if a thought spans across the boundary, the next chunk picks it up. Costs a few more embeddings but context stays intact.

```
📄 → [──── 1000 chars ────]
         [──── 1000 chars ────]
              [──── 1000 chars ────]
```

**Chunks produced:** 44 (avg 986 chars each)

### 3️⃣ Semantic Chunking (`semantic.py`)
> **"Respect the paragraph breaks, people!"**

Uses LangChain's fancy `RecursiveCharacterTextSplitter`. It tries to split at natural boundaries first — paragraph breaks (`\n\n`), then newlines, then sentence endings, then words. Only as a last resort does it just chop blindly.

```
📄 → [─── Paragraph ───] [─── Paragraph ───] [Sentence 1. Sentence 2.]
```

**Chunks produced:** 49 (avg 732 chars each)

### 4️⃣ Hierarchical Chunking (`hierarchical.py`)
> **"I need STRUCTURE. Give me sections AND paragraphs."**

The overachiever. Parses markdown headings (`##`, `###`) into sections, then splits each section into paragraphs. Every tiny chunk knows which section it belongs to, so you can search at different levels. Produces a lot of small chunks but they're super targeted.

```
📄
├─ ## Authentication
│   ├─ "API keys are used for authentication..."
│   └─ "Store keys in environment variables..."
├─ ## Rate Limits
│   ├─ "You get X requests per minute..."
│   └─ "Check headers for remaining usage..."
```

**Chunks produced:** 168 (avg 205 chars each)

## 🛠️ Tech Stack

| Thing | What we used |
|-------|-------------|
| **Embeddings** | Cohere `embed-english-v3.0` (1024-dim vectors) |
| **Vector DB** | ChromaDB (persistent, local) |
| **Reranker** | Cohere `rerank-v3.5` (cross-encoder) |
| **Semantic splitter** | LangChain `RecursiveCharacterTextSplitter` |
| **Language** | Python 3 |
| **Fallback dataset** | OpenAI API docs (~5,200 words, ~35K chars) |

## 🏃 How to Run This Yourself

```bash
# 1. Install the stuff
pip install -r requirements.txt

# 2. Set your keys (choose your adventure)
export COHERE_API_KEY="your-cohere-key"

# 3. Run the whole pipeline in one shot
python run_all.py

# Or do it step by step:
python fetch_dataset.py    # Get the test document
python embed_store.py      # Chunk → Embed → ChromaDB
python evaluate.py         # Score retrieval quality (you score each query 0/1/2)
python reranker.py         # Compare vector search vs reranker
```

## 📊 What We Found

### Evaluation Scores (10 queries, scored 0/1/2 per strategy)
All strategies scored perfectly (20/20) because the embeddings were strong enough to find relevant chunks for every query. The real differentiation showed up in the reranker comparison.

### Reranker Results (Vector Search → Top-10 → Rerank → Top-3)

| Strategy | Avg Vector Score | Avg Rerank Score | Improvement |
|----------|:---------------:|:----------------:|:-----------:|
| **Fixed** | 0.5622 | 0.6035 | **+7.3%** |
| **Sliding** | 0.5878 | **0.7095** | **+20.7%**  |
| **Semantic** | 0.5983 | **0.7147** | **+19.5%** |
| **Hierarchical** | 0.6222 | 0.7070 | **+13.6%** |

### The Tea ☕

- **Semantic chunking** had the best reranked score (0.7147) — its natural boundaries gave the reranker the cleanest chunks to work with
- **Sliding window** tied for best improvement (+20.7%) — the overlap really helped the reranker find gold
- **Hierarchical** had the highest initial vector score (0.6222) — small focused chunks are easy for vector search to match
- **Fixed** was the baseline... it works, it's fine, but it doesn't win any awards
- The reranker boosted **every** strategy. Even fixed got 7% better. Moral of the story: if you can afford a reranker, use one.

## 📁 Project Layout

```
rag-chunking/
├── chunkers/
│   ├── __init__.py
│   ├── fixed.py          # Fixed-size chunker
│   ├── sliding.py        # Sliding window chunker
│   ├── semantic.py       # LangChain semantic splitter
│   └── hierarchical.py   # Two-level section → paragraph
├── data/
│   ├── raw.txt           # Source document (~5,200 words)
│   ├── chroma/           # ChromaDB persistent storage (4 collections)
│   └── metadata/         # Chunk metadata JSONs per strategy
├── fetch_dataset.py      # Gets/builds the test document
├── embed_store.py        # Chunks + embeds + stores everything
├── evaluate.py           # Interactive retrieval quality scoring
├── reranker.py           # Cohere reranker vs vector search
├── run_all.py            # Runs the full pipeline end-to-end
├── queries.json          # 10 evaluation queries
├── results.json          # Evaluation scores
├── rerank_results.json   # Reranker comparison data
├── requirements.txt      # Python dependencies
└── .env                  # API keys (you fill this in)
```

## 💡 Stuff I Learned Along the Way

- **Cohere v7 changed the API** — embeddings live at `resp.embeddings.float_` now, not `resp.embeddings[0]`. Took a minute to figure that one out.
- **ChromaDB returns Collection objects** from `list_collections()`, not strings — gotta use `.name` to check if a collection exists.
- **Free tier limits are real** — Cohere Trial key only lets you do 10 rerank calls per minute. Good to know for demos.
- **More chunks ≠ better** — Hierarchical made 168 chunks (vs 35 for fixed), but it didn't dominate the scores. Quality > quantity.
- **Rerankers are worth it** — Even a simple rerank pass gave +7-20% improvement across the board.

## 🚀 What's Next (if I keep going)

- Try it with bigger docs (100K+ words)
- Compare Cohere embeddings vs OpenAI `text-embedding-3-small`
- Add a real LLM (GPT-4o, Claude) on top to measure actual answer quality
- Try hybrid search (vector + keyword BM25)
- Build a tiny Streamlit UI to play with chunk parameters

---

*Built in a day, fueled by curiosity and too much coffee. ☕*

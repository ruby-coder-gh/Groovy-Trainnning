// ─────────────────────────────────────────────────────────────────────
// Embedder — generates embeddings for text chunks
//
// Supports two providers:
//   openai (default): text-embedding-3-small (1536-d, $0.02/1M tokens)
//   ollama:           nomic-embed-text      (768-d,  free/local)
// ─────────────────────────────────────────────────────────────────────

"use strict";

const EMBEDDING_PROVIDER = process.env.EMBEDDING_PROVIDER || "openai";
const EMBEDDING_MODEL    = process.env.EMBEDDING_MODEL    || "text-embedding-3-small";
const EMBEDDING_DIMS     = EMBEDDING_PROVIDER === "ollama" ? 768 : 1536;
const OLLAMA_HOST        = process.env.OLLAMA_HOST        || "http://localhost:11434";
const OLLAMA_EMBED_MODEL = process.env.OLLAMA_EMBED_MODEL || "nomic-embed-text";

/**
 * Generate an embedding vector for a single text string.
 */
async function embed(text) {
  if (EMBEDDING_PROVIDER === "ollama") {
    return embedOllama(text);
  }
  return embedOpenAI(text);
}

/**
 * Generate embeddings for multiple texts in batch.
 * More efficient than individual calls.
 */
async function embedBatch(texts) {
  if (texts.length === 0) return [];

  if (EMBEDDING_PROVIDER === "ollama") {
    return embedOllamaBatch(texts);
  }
  return embedOpenAIBatch(texts);
}

// ─── OpenAI Embeddings ──────────────────────────────────────────

/**
 * Single-text embedding via OpenAI.
 */
async function embedOpenAI(text) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey || apiKey === "YOUR_KEY_HERE") {
    throw new Error("A valid OPENAI_API_KEY is required for OpenAI embeddings. Set EMBEDDING_PROVIDER=ollama to use local embeddings instead.");
  }

  const res = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      input: text,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`OpenAI embedding error ${res.status}: ${err.substring(0, 200)}`);
  }

  const data = await res.json();
  return data.data[0].embedding;
}

/**
 * Batch embedding via OpenAI.
 */
async function embedOpenAIBatch(texts) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey || apiKey === "YOUR_KEY_HERE") {
    throw new Error("A valid OPENAI_API_KEY is required for OpenAI embeddings.");
  }

  const res = await fetch("https://api.openai.com/v1/embeddings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: EMBEDDING_MODEL,
      input: texts,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`OpenAI batch embedding error ${res.status}: ${err.substring(0, 200)}`);
  }

  const data = await res.json();

  // Sort by index to maintain order
  return data.data
    .sort((a, b) => a.index - b.index)
    .map((item) => item.embedding);
}

// ─── Ollama Embeddings ─────────────────────────────────────────

/**
 * Single-text embedding via Ollama.
 */
async function embedOllama(text) {
  const res = await fetch(`${OLLAMA_HOST}/api/embeddings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: OLLAMA_EMBED_MODEL,
      prompt: text,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Ollama embedding error ${res.status}: ${err.substring(0, 200)}`);
  }

  const data = await res.json();
  return data.embedding;
}

/**
 * Batch embedding via Ollama (multiple sequential calls).
 * Ollama's /api/embed (newer API) supports batch, but /api/embeddings
 * is single-input. We'll call it in parallel for simplicity.
 */
async function embedOllamaBatch(texts) {
  const results = await Promise.all(texts.map((t) => embedOllama(t)));
  return results;
}

/**
 * Compute cosine similarity between two vectors.
 * Returns -1 to 1 (1 = identical direction).
 */
function cosineSimilarity(a, b) {
  if (a.length !== b.length) return 0;

  let dot = 0, magA = 0, magB = 0;

  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }

  const denom = Math.sqrt(magA) * Math.sqrt(magB);
  return denom === 0 ? 0 : dot / denom;
}

/**
 * Compute embedding cost for a batch of texts.
 * Returns $0 for Ollama (free/local).
 */
function estimateCost(texts) {
  if (EMBEDDING_PROVIDER === "ollama") return 0;

  let totalChars = 0;
  for (const t of texts) totalChars += t.length;
  const estimatedTokens = Math.ceil(totalChars / 4);
  // text-embedding-3-small: $0.02 per 1M tokens
  return (estimatedTokens / 1_000_000) * 0.02;
}

// Re-query dynamic dims at runtime (in case env changes)
function getDims() {
  return process.env.EMBEDDING_PROVIDER === "ollama" ? 768 : 1536;
}

module.exports = {
  embed,
  embedBatch,
  cosineSimilarity,
  estimateCost,
  EMBEDDING_DIMS,
  EMBEDDING_MODEL,
  EMBEDDING_PROVIDER,
  getDims,
};

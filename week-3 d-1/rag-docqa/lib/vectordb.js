// ─────────────────────────────────────────────────────────────────────
// VectorDB — ChromaDB wrapper with JSON fallback
//
// Supports:
//   1. ChromaDB (recommended) — persistent vector storage
//   2. JSON file fallback — simple local storage, zero deps
//
// ChromaDB:  npm install chromadb
// JSON:      built-in (fs)
// ─────────────────────────────────────────────────────────────────────

"use strict";

const fs = require("fs");
const path = require("path");
const { cosineSimilarity } = require("./embedder");

const CHROMA_PATH = process.env.CHROMA_DB_PATH || "./data/chroma";

// ─── ChromaDB wrapper (tried first) ─────────────────────────────
let chromaCollection = null;
let chromaAvailable = false;

async function initChroma() {
  try {
    const { ChromaClient } = require("chromadb");
    const client = new ChromaClient({ path: `file://${path.resolve(CHROMA_PATH)}` });

    // Delete existing collection if it exists (for fresh ingest)
    try {
      await client.deleteCollection({ name: "documents" });
    } catch {}

    chromaCollection = await client.createCollection({
      name: "documents",
      metadata: { "hnsw:space": "cosine" },
    });

    chromaAvailable = true;
    console.log(`\x1b[32m✓ ChromaDB ready at ${CHROMA_PATH}\x1b[0m`);
    return true;
  } catch (err) {
    console.log(`\x1b[33m⚠ ChromaDB not available (${err.message}), using JSON fallback\x1b[0m`);
    return false;
  }
}

// ─── JSON fallback ───────────────────────────────────────────────
const JSON_DB_PATH = path.join(CHROMA_PATH, "..", "vector-store.json");

// In-memory cache to avoid repeated file reads on every query
let _memoryCache = null;
let _cacheDirty = false;

function ensureJsonDb() {
  const dir = path.dirname(JSON_DB_PATH);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (!fs.existsSync(JSON_DB_PATH)) {
    fs.writeFileSync(JSON_DB_PATH, JSON.stringify({ chunks: [], embeddings: [] }), "utf-8");
  }
}

function readJsonDb() {
  ensureJsonDb();
  // Use cached version if available, otherwise read from disk
  if (_memoryCache) return _memoryCache;
  _memoryCache = JSON.parse(fs.readFileSync(JSON_DB_PATH, "utf-8"));
  return _memoryCache;
}

function writeJsonDb(data) {
  ensureJsonDb();
  _memoryCache = data; // Update cache first
  _cacheDirty = true;
  // Write to disk (synchronously for consistency)
  fs.writeFileSync(JSON_DB_PATH, JSON.stringify(data, null, 2), "utf-8");
  _cacheDirty = false;
}

/**
 * Invalidate the in-memory cache (forces re-read from disk on next query).
 * Call this after external modifications to the JSON file.
 */
function invalidateCache() {
  _memoryCache = null;
}

// ─── Public API ─────────────────────────────────────────────────

let _initialized = false;

/**
 * Initialize the vector database (ChromaDB or JSON).
 */
async function init() {
  if (_initialized) return;
  const ok = await initChroma();
  if (!ok) ensureJsonDb();
  _initialized = true;
}

/**
 * Add chunks with their embeddings to the store.
 *
 * @param {Array<{id: string, text: string, embedding: number[], metadata: object}>} items
 */
async function addItems(items) {
  await init();

  if (chromaAvailable && chromaCollection) {
    await chromaCollection.add({
      ids: items.map((i) => i.id),
      embeddings: items.map((i) => i.embedding),
      documents: items.map((i) => i.text),
      metadatas: items.map((i) => i.metadata || {}),
    });
  } else {
    const db = readJsonDb();
    for (const item of items) {
      db.chunks.push({
        id: item.id,
        text: item.text,
        metadata: item.metadata || {},
      });
      db.embeddings.push({
        id: item.id,
        vector: item.embedding,
      });
    }
    writeJsonDb(db);
  }

  console.log(`  \x1b[36mAdded ${items.length} items to vector store\x1b[0m`);
}

/**
 * Query the vector store for the top-k most similar items.
 *
 * @param {number[]} queryEmbedding - The query embedding vector
 * @param {number} k - Number of results to return (default: 3)
 * @returns {Array<{id: string, text: string, score: number, metadata: object}>}
 */
async function query(queryEmbedding, k = 3) {
  await init();

  if (chromaAvailable && chromaCollection) {
    const results = await chromaCollection.query({
      queryEmbeddings: [queryEmbedding],
      nResults: k,
    });

    const items = [];
    for (let i = 0; i < (results.ids?.[0]?.length || 0); i++) {
      items.push({
        id: results.ids[0][i],
        text: results.documents[0][i],
        score: results.distances?.[0]?.[i] !== undefined
          ? 1 - results.distances[0][i]  // convert distance to similarity
          : 0,
        metadata: results.metadatas?.[0]?.[i] || {},
      });
    }
    return items;
  }

  // JSON fallback — brute-force cosine similarity
  const db = readJsonDb();
  const scored = [];

  for (const entry of db.embeddings) {
    const chunk = db.chunks.find((c) => c.id === entry.id);
    if (!chunk) continue;

    const score = cosineSimilarity(queryEmbedding, entry.vector);
    // Create new objects (don't retain references to cached data beyond what's needed)
    scored.push({
      id: entry.id,
      text: chunk.text,
      score,
      metadata: chunk.metadata ? { ...chunk.metadata } : {},
    });
  }

  // Sort by score descending, take top-k
  scored.sort((a, b) => b.score - a.score);
  const topK = scored.slice(0, k);
  // Clear the full scored array to release non-top-k text references
  scored.length = 0;
  return topK;
}

/**
 * Get total count of stored chunks.
 */
async function count() {
  await init();

  if (chromaAvailable && chromaCollection) {
    return await chromaCollection.count();
  }

  const db = readJsonDb();
  return db.chunks.length;
}

/**
 * Clear all stored data.
 */
async function clear() {
  _initialized = false;
  chromaCollection = null;
  chromaAvailable = false;
  _memoryCache = null;

  if (fs.existsSync(JSON_DB_PATH)) {
    fs.unlinkSync(JSON_DB_PATH);
  }

  // Re-init ChromaDB
  const ok = await initChroma();
  if (!ok) ensureJsonDb();
  _initialized = true;

  console.log(`\x1b[33m🗑 Vector store cleared\x1b[0m`);
}

module.exports = { init, addItems, query, count, clear };

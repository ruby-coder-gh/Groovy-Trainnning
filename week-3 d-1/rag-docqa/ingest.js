#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Ingest Pipeline — PDF → Chunks → Embeddings → Vector Store
//
// Usage:
//   node ingest.js <pdf-file>
//   node ingest.js ./data/docs/manual.pdf
//   node ingest.js --chunk-size 300 --overlap 30 ./data/docs/manual.pdf
// ─────────────────────────────────────────────────────────────────────

"use strict";

const fs = require("fs");
const path = require("path");
const { parsePdf } = require("./lib/pdfParser");
const { chunkPages, estimateTokens } = require("./lib/chunker");
const { embedBatch, estimateCost } = require("./lib/embedder");
const vectordb = require("./lib/vectordb");

// ─── Config ────────────────────────────────────────────────────
const CHUNK_SIZE  = parseInt(process.env.CHUNK_SIZE  || "500", 10);
const CHUNK_OVERLAP = parseInt(process.env.CHUNK_OVERLAP || "50", 10);

// ─── CLI ────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const pdfFile = args.find((a) => !a.startsWith("--"));

const chunkSizeFlag  = args.indexOf("--chunk-size");
const CHUNK_SIZE_OVERRIDE  = chunkSizeFlag  !== -1 ? parseInt(args[chunkSizeFlag  + 1], 10) : CHUNK_SIZE;
const overlapFlag    = args.indexOf("--overlap");
const OVERLAP_OVERRIDE = overlapFlag !== -1 ? parseInt(args[overlapFlag + 1], 10) : CHUNK_OVERLAP;

if (!pdfFile) {
  console.error("\x1b[31mUsage: node ingest.js <pdf-file> [--chunk-size N] [--overlap N]\x1b[0m");
  process.exit(1);
}

// ─── Main ───────────────────────────────────────────────────────
async function main() {
  const filePath = path.resolve(pdfFile);
  if (!fs.existsSync(filePath)) {
    console.error(`\x1b[31mFile not found: ${filePath}\x1b[0m`);
    process.exit(1);
  }

  console.log(`\x1b[32m📄 RAG Ingest Pipeline — Day 11\x1b[0m`);
  console.log(`   \x1b[36mFile:\x1b[0m    ${path.basename(filePath)}`);
  console.log(`   \x1b[36mChunks:\x1b[0m  ${CHUNK_SIZE_OVERRIDE} tokens (overlap: ${OVERLAP_OVERRIDE})`);
  console.log("");

  // ── Step 1: Parse PDF ───────────────────────────────────────
  console.log(`\x1b[36m📖 Step 1: Parsing PDF...\x1b[0m`);
  const doc = await parsePdf(filePath);
  console.log(`   ${doc.totalPages} pages, ${estimateTokens(doc.fullText).toLocaleString()} estimated tokens\n`);

  // ── Step 2: Chunk ───────────────────────────────────────────
  console.log(`\x1b[36m✂️  Step 2: Chunking...\x1b[0m`);
  const chunks = chunkPages(doc.pages, {
    chunkSize: CHUNK_SIZE_OVERRIDE,
    overlap: OVERLAP_OVERRIDE,
  });
  console.log(`   ${chunks.length} chunks created\n`);

  // Show first few chunks in verbose mode
  if (args.includes("--verbose")) {
    for (let i = 0; i < Math.min(3, chunks.length); i++) {
      const c = chunks[i];
      console.log(`   \x1b[90mChunk ${c.index} (Page ${c.pageNumber}):\x1b[0m ${c.text.substring(0, 120)}...`);
    }
    if (chunks.length > 3) console.log(`   \x1b[90m... and ${chunks.length - 3} more chunks\x1b[0m`);
    console.log("");
  }

  // ── Step 3: Generate embeddings ─────────────────────────────
  console.log(`\x1b[36m🧠 Step 3: Generating embeddings...\x1b[0m`);
  const texts = chunks.map((c) => c.text);
  const embedCost = estimateCost(texts);
  console.log(`   Model: ${require("./lib/embedder").EMBEDDING_MODEL}`);
  console.log(`   Estimated cost: \$${embedCost.toFixed(6)}`);

  const embeddings = await embedBatch(texts);
  console.log(`   ${embeddings.length} embeddings generated (${embeddings[0]?.length || 0} dimensions)\n`);

  // ── Step 4: Store in vector DB ──────────────────────────────
  console.log(`\x1b[36m💾 Step 4: Storing in vector database...\x1b[0m`);

  const items = chunks.map((chunk, i) => ({
    id: `chunk-${String(chunk.index).padStart(5, "0")}`,
    text: chunk.text,
    embedding: embeddings[i],
    metadata: {
      pageNumber: chunk.pageNumber,
      source: chunk.source,
      chunkIndex: chunk.index,
    },
  }));

  await vectordb.addItems(items);
  const totalCount = await vectordb.count();
  console.log(`   \x1b[32m✓ Total chunks in store: ${totalCount}\x1b[0m\n`);

  // ── Summary ─────────────────────────────────────────────────
  const totalTokens = chunks.reduce((s, c) => s + estimateTokens(c.text), 0);
  console.log(`\x1b[32m╔═══════════════════════════════════════════════╗\x1b[0m`);
  console.log(`\x1b[32m║        📊 Ingest Complete                     ║\x1b[0m`);
  console.log(`\x1b[32m╚═══════════════════════════════════════════════╝\x1b[0m`);
  console.log(`   File:         ${path.basename(filePath)}`);
  console.log(`   Pages:        ${doc.totalPages}`);
  console.log(`   Chunks:       ${chunks.length}`);
  console.log(`   Total tokens: ${totalTokens.toLocaleString()}`);
  console.log(`   Embed cost:   \$${embedCost.toFixed(6)}`);
  console.log(`   Store:        ${process.env.CHROMA_DB_PATH || "./data/chroma"}`);
  console.log("");

  // Save metadata for cost comparison
  const meta = {
    fileName: path.basename(filePath),
    totalPages: doc.totalPages,
    totalChunks: chunks.length,
    totalTokens,
    embedCost,
    chunkSize: CHUNK_SIZE_OVERRIDE,
    overlap: OVERLAP_OVERRIDE,
    ingestedAt: new Date().toISOString(),
  };
  const metaPath = path.join(path.dirname(filePath), ".ingest-meta.json");
  fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2), "utf-8");
  console.log(`   \x1b[90mMetadata saved to ${metaPath}\x1b[0m\n`);
}

main().catch((err) => {
  console.error(`\x1b[31mIngest failed: ${err.message}\x1b[0m`);
  process.exit(1);
});

#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Cosine Similarity Interactive Demo
//
// Shows how embeddings are generated and compared using cosine similarity.
// Try different word pairs to see semantic relationships.
// ─────────────────────────────────────────────────────────────────────

"use strict";

const readline = require("readline");

// ─── Tiny embedder (dummy embedding for demo without API key) ──────
// In production, use OpenAI text-embedding-3-small.
// Here we generate a simple random embedding for illustration.
function generateDemoEmbedding(text, dims = 16) {
  // Seed-based so same text gets same embedding
  let seed = 0;
  for (let i = 0; i < text.length; i++) {
    seed = ((seed << 5) - seed) + text.charCodeAt(i);
    seed = seed & seed; // Convert to 32-bit integer
  }

  const vec = [];
  for (let i = 0; i < dims; i++) {
    // Generate deterministic pseudo-random values
    const val = Math.sin(seed * (i + 1) * 13.37) * 10000;
    vec.push(val - Math.floor(val));
  }

  // Normalize to unit vector
  const mag = Math.sqrt(vec.reduce((s, v) => s + v * v, 0));
  return vec.map((v) => v / mag);
}

// ─── Cosine Similarity ────────────────────────────────────────────
function cosineSimilarity(a, b) {
  if (a.length !== b.length) {
    throw new Error("Vectors must have the same dimension");
  }

  let dotProduct = 0;
  let magA = 0;
  let magB = 0;

  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }

  const magnitude = Math.sqrt(magA) * Math.sqrt(magB);
  if (magnitude === 0) return 0;

  return dotProduct / magnitude;
}

// ─── Interactive Demo ──────────────────────────────────────────────
function printBreakdown(word1, word2) {
  const vec1 = generateDemoEmbedding(word1, 16);
  const vec2 = generateDemoEmbedding(word2, 16);
  const sim = cosineSimilarity(vec1, vec2);

  console.log(`\n  \x1b[36mWord 1:\x1b[0m "${word1}"`);
  console.log(`  \x1b[36mWord 2:\x1b[0m "${word2}"`);
  console.log(`  \x1b[36mSimilarity:\x1b[0m ${(sim * 100).toFixed(2)}%`);
  console.log(`  \x1b[36mInterpretation:\x1b[0m ${interpretSimilarity(sim)}`);

  if (sim > 0.5) {
    console.log(`  \x1b[32m  ✓ These words are semantically related\x1b[0m`);
  } else if (sim > 0) {
    console.log(`  \x1b[33m  △ Weak or no semantic relationship\x1b[0m`);
  } else {
    console.log(`  \x1b[31m  ✗ These words are semantically opposite\x1b[0m`);
  }

  // Print vectors
  console.log(`\n  \x1b[90mEmbedding 1 (first 8 dims): [${vec1.slice(0, 8).map((v) => v.toFixed(4)).join(", ")}...]\x1b[0m`);
  console.log(`  \x1b[90mEmbedding 2 (first 8 dims): [${vec2.slice(0, 8).map((v) => v.toFixed(4)).join(", ")}...]\x1b[0m`);
}

function interpretSimilarity(sim) {
  if (sim > 0.95) return "Nearly identical meaning";
  if (sim > 0.8) return "Very strong semantic similarity";
  if (sim > 0.6) return "Strong semantic similarity";
  if (sim > 0.4) return "Moderate semantic similarity";
  if (sim > 0.2) return "Weak semantic similarity";
  if (sim > 0) return "Barely similar";
  if (sim > -0.2) return "Very weakly opposite";
  if (sim > -0.4) return "Mildly opposite";
  if (sim > -0.6) return "Moderately opposite";
  return "Strongly opposite";
}

// ─── Preset Examples ──────────────────────────────────────────────
function runPresets() {
  console.log(`\n  \x1b[33m═══ Semantic Similarity Presets ═══\x1b[0m\n`);
  const pairs = [
    ["king", "queen"],
    ["king", "man"],
    ["king", "apple"],
    ["computer", "laptop"],
    ["computer", "carrot"],
    ["dog", "puppy"],
    ["dog", "cat"],
    ["hot", "cold"],
    ["hot", "warm"],
    ["hot", "volcano"],
    ["run", "running"],
    ["run", "sit"],
    ["ocean", "sea"],
    ["ocean", "desk"],
    ["JavaScript", "Java"],
    ["JavaScript", "coffee"],
  ];

  for (const [w1, w2] of pairs) {
    printBreakdown(w1, w2);
    console.log("");
  }
}

// ─── Main ──────────────────────────────────────────────────────────
function main() {
  const args = process.argv.slice(2);

  console.log(`
  ╔══════════════════════════════════════════════╗
  ║   Cosine Similarity Interactive Demo         ║
  ║   Shows how embeddings capture meaning       ║
  ╚══════════════════════════════════════════════╝
  `);

  console.log(`  \x1b[90mFormula: cos(θ) = A·B / (∥A∥·∥B∥)\x1b[0m`);
  console.log(`  \x1b[90mRange:   [-1, 1] where 1 = identical direction\x1b[0m`);
  console.log(`  \x1b[90mDims:    16 (for demo; real embeddings use 1536)\x1b[0m\n`);

  if (args.length === 0) {
    runPresets();
    console.log(`  \x1b[33mTry custom words: node examples/cosine-similarity.js "word1" "word2"\x1b[0m\n`);
    return;
  }

  if (args.length === 2) {
    printBreakdown(args[0], args[1]);
    console.log("");
    return;
  }

  // Interactive mode
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: "\x1b[36mEnter two words (space-separated):\x1b[0m ",
  });

  console.log(`  Type two words to see their cosine similarity.`);
  console.log(`  Type \x1b[33mpresets\x1b[0m for built-in examples, or \x1b[33mexit\x1b[0m to quit.\n`);

  rl.prompt();

  rl.on("line", (input) => {
    const text = input.trim();

    if (text === "exit" || text === "quit") {
      rl.close();
      return;
    }

    if (text === "presets") {
      runPresets();
      rl.prompt();
      return;
    }

    const parts = text.split(/\s+/);
    if (parts.length < 2) {
      console.log(`  \x1b[33mPlease enter two words separated by a space.\x1b[0m`);
      rl.prompt();
      return;
    }

    printBreakdown(parts[0], parts.slice(1).join(" "));
    console.log("");
    rl.prompt();
  });

  rl.on("close", () => {
    console.log(`\n  \x1b[32m👋 Bye!\x1b[0m\n`);
  });
}

main();

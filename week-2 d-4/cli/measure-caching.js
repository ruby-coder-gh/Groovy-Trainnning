#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Day 9 — Measure Anthropic Prompt Caching Savings
//
// Sends 3 identical requests with prompt caching enabled.
// Shows cost comparison: first request (cache write) vs subsequent (cache read).
//
// Usage:
//   export ANTHROPIC_API_KEY=sk-ant-...
//   node measure-caching.js
// ─────────────────────────────────────────────────────────────────────

"use strict";

const API_KEY = process.env.ANTHROPIC_API_KEY;
if (!API_KEY) {
  console.error("\x1b[31mError: ANTHROPIC_API_KEY not set\x1b[0m");
  process.exit(1);
}

const SYSTEM_PROMPT = "You are a helpful assistant. Respond concisely in 1-2 sentences.";
const LARGE_CONTEXT = `
The Python programming language was created by Guido van Rossum and first released in 1991.
Python's design philosophy emphasizes code readability with its notable use of significant indentation.
Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects.

Python is dynamically type-checked and garbage-collected. It supports multiple programming paradigms,
including structured (particularly procedural), object-oriented and functional programming.
It is often described as a "batteries included" language due to its comprehensive standard library.

Python consistently ranks as one of the most popular programming languages and has gained widespread adoption
in the data science and machine learning communities. Major web frameworks like Django and Flask are written in Python.
`.repeat(50); // Make it large enough to cache (>1024 tokens)

const QUESTIONS = [
  "What are the key features of Python?",
  "Who created Python and when?",
  "Why is Python popular in data science?",
];

async function callWithCaching(question, requestNum) {
  const body = {
    model: "claude-sonnet-4-20250514",
    max_tokens: 200,
    system: [
      {
        type: "text",
        text: SYSTEM_PROMPT,
        cache_control: { type: "ephemeral" },
      },
    ],
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: `Context:\n${LARGE_CONTEXT}\n\nQuestion: ${question}`,
            cache_control: { type: "ephemeral" },
          },
        ],
      },
    ],
  };

  const start = Date.now();
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY,
      "anthropic-version": "2023-06-01",
      "anthropic-beta": "prompt-caching-2024-07-31",
    },
    body: JSON.stringify(body),
  });

  const elapsed = Date.now() - start;
  const data = await res.json();
  const usage = data.usage || {};
  const cacheHit = res.headers.get("anthropic-cache-hit") || "none";

  return {
    requestNum,
    question: question.substring(0, 50),
    elapsed,
    status: res.status,
    cacheHit,
    inputTokens: usage.input_tokens || 0,
    outputTokens: usage.output_tokens || 0,
    cacheCreation: usage.cache_creation_input_tokens || 0,
    cacheRead: usage.cache_read_input_tokens || 0,
  };
}

async function main() {
  console.log(`\x1b[32m📊 Anthropic Prompt Caching — Cost Measurement\x1b[0m\n`);

  const results = [];

  for (let i = 0; i < QUESTIONS.length; i++) {
    console.log(`\x1b[36m[${i + 1}/${QUESTIONS.length}]\x1b[0m Sending request: "${QUESTIONS[i].substring(0, 50)}..."`);
    const result = await callWithCaching(QUESTIONS[i], i + 1);
    results.push(result);
    console.log(`   Status: ${result.status} · Cache: ${result.cacheHit} · ${result.elapsed}ms`);
    console.log(`   Tokens: ${result.inputTokens} in · ${result.outputTokens} out · ` +
                `Cache create: ${result.cacheCreation} · Cache read: ${result.cacheRead}`);
    console.log("");
    // Small delay between requests
    if (i < QUESTIONS.length - 1) {
      await new Promise((r) => setTimeout(r, 1000));
    }
  }

  // ── Cost Analysis ──────────────────────────────────────────
  console.log(`\x1b[32m═══════════════════════════════════════════════════════\x1b[0m`);
  console.log(`\x1b[32m               💰 Cost Savings Analysis               \x1b[0m`);
  console.log(`\x1b[32m═══════════════════════════════════════════════════════\x1b[0m\n`);

  // Claude Sonnet 4 pricing
  const STD_IN = 3.0;     // $/1M tokens
  const CACHE_WRITE = 3.75;
  const CACHE_READ = 0.30;
  const OUT = 15.0;

  console.log(`  \x1b[36mPricing (Claude Sonnet 4):\x1b[0m`);
  console.log(`    Standard input:  \$${STD_IN}/1M tokens`);
  console.log(`    Cache write:     \$${CACHE_WRITE}/1M tokens (+25%)`);
  console.log(`    Cache read:      \$${CACHE_READ}/1M tokens (-90%)`);
  console.log(`    Output:          \$${OUT}/1M tokens\n`);

  let totalActualCost = 0;
  let totalNoCacheCost = 0;

  console.log(`  \x1b[36mPer-Request Breakdown:\x1b[0m`);
  console.log(`  ${"#".padStart(3)} ${"Cache".padEnd(10)} ${"In Tokens".padEnd(12)} ${"Out Tokens".padEnd(12)} ${"Actual Cost".padEnd(14)} ${"No-Cache Cost".padEnd(14)} ${"Savings".padEnd(10)}`);
  console.log(`  ${"-".repeat(75)}`);

  for (const r of results) {
    const actualCost =
      (r.cacheCreation / 1_000_000) * CACHE_WRITE +
      (r.cacheRead / 1_000_000) * CACHE_READ +
      (Math.max(0, r.inputTokens - r.cacheCreation - r.cacheRead) / 1_000_000) * STD_IN +
      (r.outputTokens / 1_000_000) * OUT;

    const noCacheCost =
      (r.inputTokens / 1_000_000) * STD_IN +
      (r.outputTokens / 1_000_000) * OUT;

    totalActualCost += actualCost;
    totalNoCacheCost += noCacheCost;

    const savings = ((noCacheCost - actualCost) / noCacheCost * 100).toFixed(1);
    const cacheLabel = r.cacheRead > 0 ? "✅ READ" : "💾 WRITE";

    console.log(
      `  ${String(r.requestNum).padStart(3)} ` +
      `${cacheLabel.padEnd(10)} ` +
      `${String(r.inputTokens).padStart(10)} ` +
      `${String(r.outputTokens).padStart(10)} ` +
      `\$${actualCost.toFixed(6).padStart(10)} ` +
      `\$${noCacheCost.toFixed(6).padStart(10)} ` +
      `${savings.padStart(5)}%`
    );
  }

  console.log(`  ${"-".repeat(75)}`);
  const totalSavings = ((totalNoCacheCost - totalActualCost) / totalNoCacheCost * 100).toFixed(1);
  console.log(
    `  \x1b[1mTotal:\x1b[0m` +
    `${"".padStart(10)}` +
    `${"".padStart(12)}` +
    `${"".padStart(12)}` +
    ` \$${totalActualCost.toFixed(6).padStart(10)}` +
    ` \$${totalNoCacheCost.toFixed(6).padStart(10)}` +
    ` \x1b[32m${totalSavings.padStart(5)}%\x1b[0m`
  );

  console.log("");
  if (results.some((r) => r.cacheRead > 0)) {
    console.log(`  \x1b[32m✅ Prompt caching is working! Cache read detected on subsequent requests.\x1b[0m`);
  } else {
    console.log(`  \x1b[33m⚠  No cache reads detected. The context may be too small (<1024 tokens) or TTL expired.\x1b[0m`);
  }
  console.log(`\n  \x1b[90mNote: First request always pays the cache write premium.\x1b[0m`);
  console.log(`  \x1b[90m      Savings start from request #2 onwards.\x1b[0m`);
  console.log("");
}

main().catch(console.error);

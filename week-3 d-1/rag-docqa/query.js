#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Query Pipeline — Question → Embed → Retrieve Top 3 → LLM → Answer
//
// Usage:
//   node query.js "What is this document about?"
//   node query.js "How does authentication work?" --provider openai
//   node query.js --top-k 5 "Explain the architecture"
//   node query.js --interactive              # chat mode
// ─────────────────────────────────────────────────────────────────────

"use strict";

const readline = require("readline");
const { embed, cosineSimilarity } = require("./lib/embedder");
const vectordb = require("./lib/vectordb");
const { Telemetry } = require("../../week-2 d-4/telemetry/logger");

// ─── Config ────────────────────────────────────────────────────
const LLM_PROVIDER = process.env.LLM_PROVIDER || "openai";
const LLM_MODEL    = process.env.LLM_MODEL    || "gpt-4o-mini";
const TOP_K        = parseInt(process.env.TOP_K || "3", 10);

// ─── Telemetry ─────────────────────────────────────────────────
const telemetry = new Telemetry("./data/telemetry.csv", false);

// ─── CLI ────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const isInteractive = args.includes("--interactive");
const topKFlag = args.indexOf("--top-k");
const TOP_K_OVERRIDE = topKFlag !== -1 ? parseInt(args[topKFlag + 1], 10) : TOP_K;

// Collect question (all non-flag args)
const question = args.filter((a) => !a.startsWith("--")).join(" ");

// ─── System prompt for RAG answering ───────────────────────────
const SYSTEM_PROMPT = `You are a precise document Q&A assistant powered by RAG (Retrieval-Augmented Generation).

You are given a user question and a set of relevant document chunks retrieved via semantic search.
Answer the question based ONLY on the provided chunks.

Rules:
1. For every claim, cite the source like [Page N] or [Source: Page N]
2. If the chunks don't contain enough information, say "I couldn't find enough information in the document to answer that."
3. Be concise but thorough
4. Use bullet points when listing multiple items
5. If quoting directly, use "quotes" and cite the page`;

// ─── Build context from retrieved chunks ──────────────────────
function buildContext(chunks) {
  return chunks
    .map((c, i) => `[Chunk ${i + 1}] (Source: Page ${c.metadata?.pageNumber || "?"}, similarity: ${(c.score * 100).toFixed(1)}%)\n${c.text}`)
    .join("\n\n---\n\n");
}

// ─── Answer using LLM ─────────────────────────────────────────
async function answerWithLLM(question, chunks) {
  const context = buildContext(chunks);
  const userPrompt = `Question: ${question}\n\nRelevant document chunks:\n\n${context}\n\nAnswer the question based on these chunks. Cite your sources.`;

  const startTime = Date.now();
  let result;

  if (LLM_PROVIDER === "openai") {
    result = await callOpenAI(userPrompt);
  } else if (LLM_PROVIDER === "anthropic") {
    result = await callAnthropic(userPrompt);
  } else {
    result = await callOllama(userPrompt);
  }

  const elapsed = Date.now() - startTime;

  // Log telemetry
  telemetry.log({
    provider: LLM_PROVIDER,
    model: LLM_MODEL,
    promptTokens: result.inputTokens,
    completionTokens: result.outputTokens,
    cost: result.cost,
    latencyMs: elapsed,
    status: "success",
    promptType: "rag_query",
    notes: `top_k=${chunks.length}`,
  });

  return result;
}

// ─── OpenAI Caller ─────────────────────────────────────────────
async function callOpenAI(userPrompt) {
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: LLM_MODEL,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: userPrompt },
      ],
      max_tokens: 1024,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`OpenAI error ${res.status}: ${err.substring(0, 200)}`);
  }

  const data = await res.json();
  const inTokens = data.usage?.prompt_tokens || 0;
  const outTokens = data.usage?.completion_tokens || 0;

  // gpt-4o-mini pricing
  const cost = (inTokens / 1_000_000) * 0.15 + (outTokens / 1_000_000) * 0.60;

  return {
    text: data.choices[0].message.content,
    inputTokens: inTokens,
    outputTokens: outTokens,
    cost,
  };
}

// ─── Anthropic Caller (with prompt caching) ─────────────────────
async function callAnthropic(userPrompt) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": process.env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 1024,
      system: [{ type: "text", text: SYSTEM_PROMPT }],
      messages: [{ role: "user", content: userPrompt }],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic error ${res.status}: ${err.substring(0, 200)}`);
  }

  const data = await res.json();
  const inTokens = data.usage?.input_tokens || 0;
  const outTokens = data.usage?.output_tokens || 0;
  const cost = (inTokens / 1_000_000) * 3.0 + (outTokens / 1_000_000) * 15.0;

  const text = data.content?.map((b) => b.text).join("") || "";
  return { text, inputTokens: inTokens, outputTokens: outTokens, cost };
}

// ─── Ollama Caller ──────────────────────────────────────────────
async function callOllama(userPrompt) {
  const res = await fetch("http://localhost:11434/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: process.env.OLLAMA_MODEL || "qwen3:8b",
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: userPrompt },
      ],
      stream: false,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Ollama error ${res.status}: ${err.substring(0, 200)}`);
  }

  const data = await res.json();
  const inTokens = data.prompt_eval_count || 0;
  const outTokens = data.eval_count || 0;

  return {
    text: data.message?.content || "",
    inputTokens: inTokens,
    outputTokens: outTokens,
    cost: 0,
  };
}

// ─── Main Query Flow ──────────────────────────────────────────
async function runQuery(question, k = TOP_K_OVERRIDE) {
  if (!question) {
    console.error("\x1b[31mUsage: node query.js \"your question\"\x1b[0m");
    console.error("   or: node query.js --interactive");
    process.exit(1);
  }

  console.log(`\x1b[32m🔍 RAG Query Pipeline — Day 11\x1b[0m`);
  console.log(`   \x1b[36mQuestion:\x1b[0m ${question}`);
  console.log(`   \x1b[36mTop-K:\x1b[0m    ${k}`);
  console.log(`   \x1b[36mLLM:\x1b[0m      ${LLM_PROVIDER} (${LLM_MODEL})`);
  console.log("");

  // ── Step 1: Embed the question ─────────────────────────────
  console.log(`\x1b[36m🧠 Step 1: Embedding question...\x1b[0m`);
  const queryEmbedding = await embed(question);
  console.log(`   Done (${queryEmbedding.length} dimensions)\n`);

  // ── Step 2: Retrieve top-k chunks ──────────────────────────
  console.log(`\x1b[36m📂 Step 2: Retrieving top ${k} chunks...\x1b[0m`);
  const chunks = await vectordb.query(queryEmbedding, k);
  console.log(`   Found ${chunks.length} relevant chunks\n`);

  if (chunks.length === 0) {
    console.log("\x1b[33mNo relevant chunks found. Ingest a document first.\x1b[0m");
    return;
  }

  // Print retrieved chunks
  console.log(`  \x1b[33m── Retrieved Chunks ──\x1b[0m\n`);
  for (const c of chunks) {
    const sim = (c.score * 100).toFixed(1);
    const page = c.metadata?.pageNumber || "?";
    console.log(`  \x1b[36m[Chunk ${c.id}] (Page ${page}, similarity: ${sim}%)\x1b[0m`);
    console.log(`  ${c.text.substring(0, 200)}${c.text.length > 200 ? "..." : ""}`);
    console.log("");
  }

  // ── Step 3: Generate answer ────────────────────────────────
  console.log(`\x1b[36m🤖 Step 3: Generating answer (${LLM_PROVIDER})...\x1b[0m\n`);
  const result = await answerWithLLM(question, chunks);

  // ── Output ─────────────────────────────────────────────────
  console.log(result.text);
  console.log("");

  // ── Cost & Telemetry ───────────────────────────────────────
  const contextTokens = chunks.reduce((s, c) => s + Math.ceil(c.text.length / 4), 0);

  console.log(`\x1b[90m  ───────────────────────────────────────────────\x1b[0m`);
  console.log(`\x1b[90m  Query tokens:     ${result.inputTokens - contextTokens}\x1b[0m`);
  console.log(`\x1b[90m  Context tokens:   ${contextTokens} (${chunks.length} chunks)\x1b[0m`);
  console.log(`\x1b[90m  Response tokens:  ${result.outputTokens}\x1b[0m`);
  console.log(`\x1b[90m  Cost:             \$${result.cost.toFixed(6)}\x1b[0m`);

  // RAG vs full-doc comparison
  const fullDocTokens = await getFullDocTokens();
  if (fullDocTokens) {
    const fullDocCost = (fullDocTokens / 1_000_000) * 0.15 + (result.outputTokens / 1_000_000) * 0.60;
    const savings = ((fullDocCost - result.cost) / fullDocCost * 100).toFixed(1);
    console.log(`\x1b[90m  ───────────────────────────────────────────────\x1b[0m`);
    console.log(`\x1b[90m  💰 RAG Savings vs Full-Doc:${savings.padStart(8)}%\x1b[0m`);
    console.log(`\x1b[90m     Full-doc cost:  \$${fullDocCost.toFixed(6)}\x1b[0m`);
    console.log(`\x1b[90m     RAG cost:       \$${result.cost.toFixed(6)}\x1b[0m`);
  }
  console.log("");

  telemetry.close();
  return result;
}

// ─── Get full doc token count for comparison ──────────────────
async function getFullDocTokens() {
  try {
    const metaPath = "./data/docs/.ingest-meta.json";
    if (require("fs").existsSync(metaPath)) {
      const meta = JSON.parse(require("fs").readFileSync(metaPath, "utf-8"));
      return meta.totalTokens;
    }
  } catch {}
  return null;
}

// ─── Interactive Mode ─────────────────────────────────────────
async function interactiveMode() {
  console.log(`\x1b[32m💬 RAG Chat Mode — type your questions (or 'exit')\x1b[0m\n`);

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: "\x1b[36mQ:\x1b[0m ",
  });

  rl.prompt();

  rl.on("line", async (input) => {
    const text = input.trim();

    if (!text || text.toLowerCase() === "exit") {
      console.log("\n\x1b[32m👋 Bye!\x1b[0m");
      telemetry.close();
      rl.close();
      return;
    }

    console.log("");
    try {
      await runQuery(text);
    } catch (err) {
      console.error(`\x1b[31mError: ${err.message}\x1b[0m\n`);
    }
    rl.prompt();
  });
}

// ─── Entry ────────────────────────────────────────────────────
if (isInteractive) {
  interactiveMode();
} else if (question) {
  runQuery(question).catch((err) => {
    console.error(`\x1b[31mQuery failed: ${err.message}\x1b[0m`);
    process.exit(1);
  });
} else {
  console.log(`\x1b[33mUsage:\x1b[0m
  node query.js "What is this document about?"
  node query.js --interactive
  node query.js --top-k 5 "Explain the architecture"
  \x1b[0m`);
}

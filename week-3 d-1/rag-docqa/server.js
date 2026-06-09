#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// RAG Doc-Q&A v2 — Express Server (upgraded from v1)
//
// Uses RAG pipeline instead of sending full document every query.
// Endpoints:
//   POST /api/upload     — Upload PDF → ingest (chunk + embed + store)
//   POST /api/ask        — Ask question → retrieve top 3 → LLM → answer
//   GET  /api/document   — Current document info
//   GET  /api/cost       — Cost telemetry + RAG vs full-doc comparison
//   GET  /api/health     — Health check
// ─────────────────────────────────────────────────────────────────────

"use strict";

require("dotenv").config();

const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const http = require("http");
const https = require("https");

const { parsePdf } = require("./lib/pdfParser");
const { chunkPages, estimateTokens } = require("./lib/chunker");
const { embedBatch, estimateCost, embed, cosineSimilarity } = require("./lib/embedder");
const vectordb = require("./lib/vectordb");
const { Telemetry } = require("../../week-2 d-4/telemetry/logger");

const app = express();
const PORT = process.env.PORT || 3001;
const telemetry = new Telemetry("./data/telemetry.csv", true, 100);

// ─── Middleware ────────────────────────────────────────────────
app.use(cors());
app.use(express.json({ limit: "50mb" }));

// ─── Multer setup ─────────────────────────────────────────────
const uploadDir = path.join(__dirname, "uploads");
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadDir),
  filename: (_req, file, cb) =>
    cb(null, Date.now() + "-" + Math.round(Math.random() * 1e9) + "-" + file.originalname),
});

const upload = multer({
  storage,
  limits: { fileSize: 50 * 1024 * 1024 },
  fileFilter: (_req, file, cb) => {
    if (file.mimetype !== "application/pdf") return cb(new Error("Only PDFs allowed"));
    cb(null, true);
  },
});

// ─── Ingest state ─────────────────────────────────────────────
let ingestMeta = null;

// ─── HTTP helper (module level — NOT inside route handler) ─────
// Uses Buffer chunks to avoid V8 heap pressure from string concatenation.
// Includes timeout, error handling, response destroy, and max body limit.
const HTTP_TIMEOUT = parseInt(process.env.HTTP_TIMEOUT || "30000", 10);
const MAX_RESPONSE_BODY = 10 * 1024 * 1024; // 10MB safety limit

function httpPostJSON(url, bodyData, timeoutMs = HTTP_TIMEOUT) {
  return new Promise((resolve, reject) => {
    const isHttps = url.startsWith("https");
    const mod = isHttps ? https : http;
    const u = new URL(url);

    const opts = {
      hostname: u.hostname,
      port: u.port || (isHttps ? 443 : 80),
      path: u.pathname + u.search,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(bodyData),
      },
    };

    if (isHttps && process.env.OPENAI_API_KEY) {
      opts.headers["Authorization"] = `Bearer ${process.env.OPENAI_API_KEY}`;
    }

    let aborted = false;
    const chunks = [];
    let totalSize = 0;

    function abortWithError(errMsg) {
      if (aborted) return;
      aborted = true;
      reject(new Error(errMsg));
    }

    const req = mod.request(opts, (res) => {
      res.on("data", (chunk) => {
        if (aborted) return;
        totalSize += chunk.length;
        if (totalSize > MAX_RESPONSE_BODY) {
          abortWithError(`Response body exceeds ${MAX_RESPONSE_BODY} byte limit`);
          // Destroy both streams to release all internal buffers and socket references
          res.destroy();
          req.destroy();
          return;
        }
        chunks.push(chunk);
      });

      res.on("end", () => {
        if (aborted) return;
        // Concatenate Buffers (external memory, not V8 heap) into one
        const raw = Buffer.concat(chunks);
        // Destroy response stream to release socket and prevent agent retention
        res.destroy();
        try {
          resolve(JSON.parse(raw.toString("utf-8")));
        } catch (e) {
          abortWithError(`JSON parse error: ${e.message}`);
        }
      });

      res.on("error", (err) => {
        res.destroy();
        req.destroy();
        abortWithError(`Response stream error: ${err.message}`);
      });
    });

    req.setTimeout(timeoutMs, () => {
      req.destroy(new Error("Request timed out"));
      abortWithError(`Request timed out after ${timeoutMs}ms`);
    });

    req.on("error", (err) => {
      abortWithError(`Request failed: ${err.message}`);
    });

    req.write(bodyData);
    req.end();
  });
}

// ─── Clean up stale upload files on startup ────────────────────
try {
  const files = fs.readdirSync(uploadDir);
  for (const f of files) {
    const fp = path.join(uploadDir, f);
    try { fs.unlinkSync(fp); } catch {}
  }
  console.log(`\x1b[90m[cleanup] Removed ${files.length} stale upload(s)\x1b[0m`);
} catch {}

// ─── Routes ───────────────────────────────────────────────────

// POST /api/upload — Upload PDF, chunk, embed, store
app.post("/api/upload", (req, res) => {
  upload.single("pdf")(req, res, async (err) => {
    if (err) return res.status(400).json({ error: err.message });
    if (!req.file) return res.status(400).json({ error: "No PDF provided" });

    try {
      const filePath = req.file.path;
      const startTime = Date.now();

      // Set content type for streaming JSON lines (NDJSON) with charset
      res.setHeader("Content-Type", "application/x-ndjson; charset=utf-8");

      // Parse
      res.write(JSON.stringify({ step: "parsing", message: "Parsing PDF..." }) + "\n");
      const doc = await parsePdf(filePath);

      // Chunk
      const CHUNK_SIZE = parseInt(process.env.CHUNK_SIZE || "500", 10);
      const chunks = chunkPages(doc.pages, { chunkSize: CHUNK_SIZE });

      // Embed
      res.write(JSON.stringify({
        step: "embedding",
        message: `Generating embeddings for ${chunks.length} chunks...`,
      }) + "\n");

      const texts = chunks.map((c) => c.text);
      const embeddings = await embedBatch(texts);
      const embedCost = estimateCost(texts);

      // Store
      const items = chunks.map((chunk, i) => ({
        id: `chunk-${String(chunk.index).padStart(5, "0")}`,
        text: chunk.text,
        embedding: embeddings[i],
        metadata: { pageNumber: chunk.pageNumber, source: chunk.source, chunkIndex: chunk.index },
      }));

      await vectordb.clear();
      await vectordb.addItems(items);

      // Cleanup uploaded file (synchronous to guarantee removal)
      try { fs.unlinkSync(filePath); } catch (unlinkErr) {
        console.error(`\x1b[31m[upload] Failed to remove ${filePath}: ${unlinkErr.message}\x1b[0m`);
      }

      ingestMeta = {
        fileName: req.file.originalname,
        totalPages: doc.totalPages,
        totalChunks: chunks.length,
        totalTokens: chunks.reduce((s, c) => s + estimateTokens(c.text), 0),
        embedCost,
        ingestTime: Date.now() - startTime,
        ingestedAt: new Date().toISOString(),
      };

      // Save meta for cost comparison
      const metaPath = path.join(__dirname, "data", "docs", ".ingest-meta.json");
      const metaDir = path.dirname(metaPath);
      if (!fs.existsSync(metaDir)) fs.mkdirSync(metaDir, { recursive: true });
      fs.writeFileSync(metaPath, JSON.stringify(ingestMeta, null, 2), "utf-8");

      telemetry.log({
        provider: process.env.EMBEDDING_PROVIDER || "openai",
        model: process.env.EMBEDDING_MODEL || "text-embedding-3-small",
        promptTokens: ingestMeta.totalTokens,
        completionTokens: 0,
        cost: embedCost,
        latencyMs: ingestMeta.ingestTime,
        status: "success",
        promptType: "ingest",
        notes: `${chunks.length} chunks, ${doc.totalPages} pages`,
      });

      res.write(JSON.stringify({ step: "done", message: "Ingest complete" }) + "\n");
      res.end();

    } catch (parseErr) {
      res.status(500).json({ error: "Ingest failed: " + parseErr.message });
    }
  });
});

// POST /api/ask — RAG-powered question answering
app.post("/api/ask", async (req, res) => {
  const { question } = req.body;

  if (!question?.trim()) {
    return res.status(400).json({ error: "Question is required" });
  }

  try {
    const startTime = Date.now();

    // Embed question
    const queryEmbedding = await embed(question);

    // Retrieve top chunks
    const TOP_K = parseInt(process.env.TOP_K || "3", 10);
    const chunks = await vectordb.query(queryEmbedding, TOP_K);

    if (chunks.length === 0) {
      return res.status(400).json({
        error: "No relevant document chunks found. Upload a document first.",
      });
    }

    // Build context with page citations
    // Limit chunk text size for context (prevent memory bloat)
    const MAX_CHUNK_CHARS = 2000;
    let context = chunks
      .map((c, i) => `[Chunk ${i + 1}] (Source: Page ${c.metadata?.pageNumber || "?"}, similarity: ${(c.score * 100).toFixed(1)}%)\n${(c.text || "").substring(0, MAX_CHUNK_CHARS)}`)
      .join("\n\n---\n\n");

    // LLM prompt
    let systemPrompt =
      "You are a precise document Q&A assistant powered by RAG. " +
      "Answer based ONLY on the provided chunks. Cite sources like [Page N] for every claim. " +
      "If information is insufficient, say so.";

    let userPrompt = `Question: ${question}\n\nRelevant document chunks:\n\n${context}\n\nAnswer the question based on these chunks. Cite your sources.`;

    // Call LLM
    const LLM_PROVIDER = process.env.LLM_PROVIDER || "openai";
    const LLM_MODEL = process.env.LLM_MODEL || "gpt-4o-mini";

    let llmResult;

    if (LLM_PROVIDER === "openai") {
      const d = await httpPostJSON(
        "https://api.openai.com/v1/chat/completions",
        JSON.stringify({
          model: LLM_MODEL,
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt },
          ],
          max_tokens: 1024,
        })
      );
      const inT = d.usage?.prompt_tokens || 0;
      const outT = d.usage?.completion_tokens || 0;
      llmResult = {
        text: d.choices?.[0]?.message?.content || "",
        inputTokens: inT,
        outputTokens: outT,
        cost: (inT / 1_000_000) * 0.15 + (outT / 1_000_000) * 0.60,
      };
    } else {
      // Ollama fallback
      const d = await httpPostJSON(
        "http://localhost:11434/api/chat",
        JSON.stringify({
          model: process.env.OLLAMA_MODEL || "qwen3:8b",
          messages: [
            { role: "system", content: systemPrompt },
            { role: "user", content: userPrompt },
          ],
          stream: false,
          options: {
            num_predict: 512,
            num_ctx: 4096,
          },
        })
      );
      const content = d.message?.content || d.response || "";
      if (!content) console.error("Empty Ollama response:", JSON.stringify(d).substring(0,500));
      llmResult = {
        text: content,
        inputTokens: d.prompt_eval_count || 0,
        outputTokens: d.eval_count || 0,
        cost: 0,
      };
    }

    const elapsed = Date.now() - startTime;

    // Telemetry
    telemetry.log({
      provider: LLM_PROVIDER,
      model: LLM_MODEL,
      promptTokens: llmResult.inputTokens,
      completionTokens: llmResult.outputTokens,
      cost: llmResult.cost,
      latencyMs: elapsed,
      status: "success",
      promptType: "rag_query",
      notes: `top_k=${chunks.length}`,
    });

    // Build citations from chunk metadata
    const citations = chunks.map((c) => ({
      page: c.metadata?.pageNumber || 0,
      excerpt: c.text.substring(0, 250) + (c.text.length > 250 ? "..." : ""),
      similarity: c.score,
    }));

    // RAG vs full-doc cost comparison
    let fullDocCost = null;
    let savings = null;
    if (ingestMeta?.totalTokens) {
      fullDocCost = (ingestMeta.totalTokens / 1_000_000) * 0.15 +
                    (llmResult.outputTokens / 1_000_000) * 0.60;
      savings = ((fullDocCost - llmResult.cost) / fullDocCost * 100).toFixed(1);
    }

    // Build response (without full chunk texts to minimize retained references)
    const response = {
      answer: llmResult.text,
      citations,
      cost: {
        model: LLM_MODEL,
        inputTokens: llmResult.inputTokens,
        outputTokens: llmResult.outputTokens,
        queryCost: llmResult.cost,
        fullDocCost,
        savings: savings ? `${savings}%` : null,
      },
      retrieval: {
        chunksRetrieved: chunks.length,
        chunks: chunks.map((c) => ({
          id: c.id,
          page: c.metadata?.pageNumber,
          similarity: (c.score * 100).toFixed(1) + "%",
        })),
      },
    };

    // Release large references before sending response to help GC
    if (chunks) chunks.length = 0;  // Clear array to release text references

    // Clear context strings to free memory
    context = null;
    systemPrompt = null;
    userPrompt = null;

    res.json(response);

    // Log memory usage every query
    if (global.gc) {
      global.gc();
    }
    const mem = process.memoryUsage();
    console.log(`\x1b[90m[mem]\x1b[0m rss=${(mem.rss / 1024 / 1024).toFixed(0)}MB heap=${(mem.heapUsed / 1024 / 1024).toFixed(0)}/${(mem.heapTotal / 1024 / 1024).toFixed(0)}MB ext=${(mem.external / 1024 / 1024).toFixed(0)}MB`);

  } catch (err) {
    console.error("Ask error:", err);
    if (res.headersSent) {
      res.end();
    } else {
      res.status(500).json({ error: err.message });
    }
  }
});

// GET /api/cost — Telemetry summary
app.get("/api/cost", (_req, res) => {
  // Build comparison
  let comparison = null;
  if (ingestMeta) {
    const avgRagCost = telemetry.logs
      .filter((l) => l.promptType === "rag_query")
      .reduce((s, l) => s + l.cost, 0);
    const queryCount = telemetry.logs.filter((l) => l.promptType === "rag_query").length || 1;
    const avgRagPerQuery = avgRagCost / queryCount;

    const fullDocPerQuery = (ingestMeta.totalTokens / 1_000_000) * 0.15 + 500 / 1_000_000 * 0.60;
    const savingsPercent = ((fullDocPerQuery - avgRagPerQuery) / fullDocPerQuery * 100).toFixed(1);

    comparison = {
      fullDocTokensPerQuery: ingestMeta.totalTokens,
      ragTokensPerQuery: Math.round(ingestMeta.totalTokens / ingestMeta.totalChunks * 3),
      fullDocCostPerQuery: fullDocPerQuery,
      ragCostPerQuery: avgRagPerQuery,
      savingsPercent,
      totalChunks: ingestMeta.totalChunks,
      embedCost: ingestMeta.embedCost,
    };
  }

  res.json({
    telemetry: {
      totalCalls: telemetry.logs.length,
      totalCost: telemetry.logs.reduce((s, l) => s + l.cost, 0),
      byProvider: Object.entries(
        telemetry.logs.reduce((acc, l) => {
          acc[l.provider] = (acc[l.provider] || 0) + 1;
          return acc;
        }, {})
      ).map(([provider, calls]) => ({ provider, calls })),
    },
    costComparison: comparison,
  });
});

// GET /api/document — Current doc info
app.get("/api/document", (_req, res) => {
  if (!ingestMeta) return res.json({ document: null });
  res.json({
    document: {
      fileName: ingestMeta.fileName,
      totalPages: ingestMeta.totalPages,
      totalChunks: ingestMeta.totalChunks,
      ingestedAt: ingestMeta.ingestedAt,
    },
  });
});

// POST /api/clear — Clear document and vector store
app.post("/api/clear", async (_req, res) => {
  try {
    await vectordb.clear();
    ingestMeta = null;
    // Remove ingest meta file
    const metaPath = path.join(__dirname, "data", "docs", ".ingest-meta.json");
    try { fs.unlinkSync(metaPath); } catch {}
    console.log("\x1b[33m🗑 Document cleared\x1b[0m");
    res.json({ status: "ok", message: "Document cleared" });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// GET /api/health
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", rag: true, timestamp: new Date().toISOString() });
});

// ─── Serve Frontend ────────────────────────────────────────────
const publicDir = path.join(__dirname, "public");
if (fs.existsSync(publicDir)) {
  app.use(express.static(publicDir));
  // SPA fallback: serve index.html for all non-API routes
  app.get("*", (_req, res) => {
    const indexPath = path.join(publicDir, "index.html");
    if (fs.existsSync(indexPath)) {
      res.sendFile(indexPath);
    } else {
      res.status(404).json({ error: "Frontend not built yet" });
    }
  });
}

// ─── Start ────────────────────────────────────────────────────
async function start() {
  await vectordb.init();
  const storeCount = await vectordb.count();

  app.listen(PORT, () => {
    console.log(`
  ╔══════════════════════════════════════════════╗
  ║   RAG Doc-Q&A v2 — Server (Day 11)          ║
  ║   Listening on http://localhost:${PORT}        ║
  ║   Endpoints:                                 ║
  ║     POST /api/upload   — Upload PDF + Ingest ║
  ║     POST /api/ask      — RAG Question Answer ║
  ║     GET  /api/cost     — Cost + Comparison   ║
  ║     GET  /api/health   — Health check        ║
  ║                                             ║
  ║   Vector store: ${String(storeCount).padStart(5)} chunks ready      ║
  ╚══════════════════════════════════════════════╝
    `);
  });
}

start().catch(console.error);

#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Day 8 / Week 2 Day 3 — Production-Grade CLI Chatbot v2
// Streaming · Async · Retry · Token Counting · Error Handling
//
// Usage:
//   node index.js                              # default: ollama
//   node index.js --provider openai
//   node index.js --provider gemini
//   node index.js --provider openai --model gpt-4o-mini
//   node index.js --log-level debug
//   node index.js --retry-max 5
//
// Environment variables:
//   OPENAI_API_KEY         — required for OpenAI
//   GEMINI_API_KEY         — required for Gemini
//   CLI_LOG_LEVEL          — debug | info | warn | error
//   CLI_RETRY_MAX          — max retry attempts (default: 3)
// ─────────────────────────────────────────────────────────────────────

"use strict";

const readline = require("readline");
const fs = require("fs");
const path = require("path");

// ═════════════════════════════════════════════════════════════════════
// 1. CONFIGURATION
// ═════════════════════════════════════════════════════════════════════

function parseArgs() {
  const args = process.argv.slice(2);
  const get = (flag) => {
    const i = args.indexOf(flag);
    return i !== -1 && args[i + 1] ? args[i + 1] : null;
  };
  return {
    provider: (get("--provider") || "ollama").toLowerCase(),
    model: get("--model"),
    logLevel: get("--log-level") || process.env.CLI_LOG_LEVEL || "info",
    retryMax: parseInt(get("--retry-max") || process.env.CLI_RETRY_MAX || "3", 10),
    noStream: args.includes("--no-stream"),
    historyFile: get("--history") || null,
  };
}

const CFG = parseArgs();

// ═════════════════════════════════════════════════════════════════════
// 2. LOGGER
// ═════════════════════════════════════════════════════════════════════

const LOG_LEVELS = { silent: 0, error: 1, warn: 2, info: 3, debug: 4 };
const currentLogLevel = LOG_LEVELS[CFG.logLevel] ?? LOG_LEVELS.info;

const log = {
  error: (...args) => currentLogLevel >= LOG_LEVELS.error && console.error("\x1b[31m[ERROR]\x1b[0m", ...args),
  warn:  (...args) => currentLogLevel >= LOG_LEVELS.warn  && console.warn("\x1b[33m[WARN]\x1b[0m",  ...args),
  info:  (...args) => currentLogLevel >= LOG_LEVELS.info  && console.log("\x1b[36m[INFO]\x1b[0m",  ...args),
  debug: (...args) => currentLogLevel >= LOG_LEVELS.debug && console.log("\x1b[90m[DEBUG]\x1b[0m", ...args),
};

// ═════════════════════════════════════════════════════════════════════
// 3. RETRY — Exponential Backoff with Jitter
// ═════════════════════════════════════════════════════════════════════

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Calculate delay with exponential backoff + full jitter.
 * Formula: delay = min(cap, base * 2^attempt)  then  random(0, delay)
 */
function backoffDelay(attempt, baseMs = 1000, maxMs = 60000) {
  const exp = Math.min(maxMs, baseMs * Math.pow(2, attempt));
  return Math.random() * exp; // full jitter
}

/**
 * Retry wrapper — retries async fn on retryable errors.
 * Retryable: 429 (rate limit), 500, 502, 503, 504, and network errors.
 */
async function withRetry(fn, options = {}) {
  const maxRetries = options.retries ?? CFG.retryMax;
  const baseMs = options.baseMs ?? 1000;
  const maxMs = options.maxMs ?? 60000;

  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn(attempt);
    } catch (err) {
      lastError = err;

      // Determine if retryable
      const status = err.status || err.code;
      const isRetryable =
        status === 429 ||
        status === 500 ||
        status === 502 ||
        status === 503 ||
        status === 504 ||
        status === "ECONNRESET" ||
        status === "ETIMEDOUT" ||
        status === "FETCH_ERROR";

      if (!isRetryable || attempt >= maxRetries) {
        throw err; // non-retryable or out of attempts
      }

      const delay = backoffDelay(attempt, baseMs, maxMs);
      log.warn(`Attempt ${attempt + 1}/${maxRetries} failed (${err.message}). Retrying in ${(delay / 1000).toFixed(1)}s...`);
      await sleep(delay);
    }
  }

  throw lastError;
}

// ═════════════════════════════════════════════════════════════════════
// 4. TOKEN COUNTER
// ═════════════════════════════════════════════════════════════════════

/**
 * Approximate token counter — ~4 chars per token for English text.
 * Uses optional tiktoken npm package if available for accuracy.
 */
let tiktokenEncoding = null;
try {
  const tiktoken = require("tiktoken");
  tiktokenEncoding = tiktoken.encoding_for_model("gpt-4o-mini");
  log.debug("tiktoken loaded for accurate token counting");
} catch {
  log.debug("tiktoken not available, using approximate counting");
}

function countTokens(text) {
  if (!text) return 0;
  if (tiktokenEncoding) {
    return tiktokenEncoding.encode(text).length;
  }
  // Approximate: ~4 chars per token for English
  return Math.ceil(text.length / 4);
}

function countMessageTokens(messages) {
  let total = 0;
  for (const m of messages) {
    total += countTokens(m.content || "");
    // Role tokens: ~4 per message overhead
    total += 4;
  }
  // Base format tokens
  total += 3;
  return total;
}

// ═════════════════════════════════════════════════════════════════════
// 5. PROVIDER DEFINITIONS
// ═════════════════════════════════════════════════════════════════════

const PROVIDERS = {
  openai: {
    name: "OpenAI",
    defaultModel: "gpt-4o-mini",
    url: "https://api.openai.com/v1/chat/completions",
    headers: () => ({
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.OPENAI_API_KEY || ""}`,
    }),
    costPer1MIn: 0.15,
    costPer1MOut: 0.60,

    buildBody(messages, model, stream) {
      return {
        model,
        messages,
        stream,
        // Include functions on first message to demo function calling
        functions: messages.length <= 2 ? [
          {
            name: "get_weather",
            description: "Get current weather for a city",
            parameters: {
              type: "object",
              properties: {
                city: { type: "string" },
                unit: { type: "string", enum: ["celsius", "fahrenheit"] },
              },
              required: ["city"],
            },
          },
        ] : undefined,
        function_call: "auto",
      };
    },

    /**
     * Parse OpenAI SSE stream.
     * Format: data: {"choices":[{"delta":{"content":"..."}}]}
     *         data: [DONE]
     */
    async *parseStream(response) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // keep incomplete line

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith("data: ")) continue;
            const payload = trimmed.slice(6);
            if (payload === "[DONE]") return;

            try {
              const chunk = JSON.parse(payload);
              const content = chunk.choices?.[0]?.delta?.content;
              if (content) yield content;
            } catch {
              // skip malformed JSON chunks
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },

    parseUsage(data) {
      return data.usage
        ? { in: data.usage.prompt_tokens, out: data.usage.completion_tokens }
        : null;
    },
  },

  gemini: {
    name: "Gemini",
    defaultModel: "gemini-2.0-flash",
    url: (model) =>
      `https://generativelanguage.googleapis.com/v1beta/models/${model}:streamGenerateContent?alt=sse&key=${process.env.GEMINI_API_KEY || ""}`,
    headers: () => ({ "Content-Type": "application/json" }),
    costPer1MIn: 0.075,
    costPer1MOut: 0.30,

    buildBody(messages, model, stream) {
      return {
        contents: messages.map((m) => ({
          role: m.role === "assistant" ? "model" : m.role,
          parts: [{ text: m.content || "" }],
        })),
      };
    },

    /**
     * Parse Gemini SSE stream.
     * Format: data: {"candidates":[{"content":{"parts":[{"text":"..."}]}}]}
     */
    async *parseStream(response) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed || !trimmed.startsWith("data: ")) continue;
            const payload = trimmed.slice(6);
            if (!payload || payload === "[DONE]") continue;

            try {
              const chunk = JSON.parse(payload);
              const text = chunk.candidates?.[0]?.content?.parts?.[0]?.text;
              if (text) yield text;
            } catch {
              // skip malformed
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },

    parseUsage(data) {
      if (data.usageMetadata) {
        return {
          in: data.usageMetadata.promptTokenCount || 0,
          out: data.usageMetadata.candidatesTokenCount || 0,
        };
      }
      return null;
    },
  },

  ollama: {
    name: "Ollama",
    defaultModel: "qwen3:8b",
    url: "http://localhost:11434/api/chat",
    headers: () => ({ "Content-Type": "application/json" }),
    costPer1MIn: 0,
    costPer1MOut: 0,

    buildBody(messages, model, stream) {
      return { model, messages, stream };
    },

    /**
     * Parse Ollama NDJSON stream (not SSE).
     * Format: {"message":{"role":"assistant","content":"..."},"done":false}
     *         {"message":{"role":"assistant","content":""},"done":true,...}
     */
    async *parseStream(response) {
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            try {
              const chunk = JSON.parse(trimmed);
              const content = chunk.message?.content || "";
              if (content) yield content;
            } catch {
              // skip malformed
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    },

    parseUsage(data) {
      if (data.prompt_eval_count != null) {
        return { in: data.prompt_eval_count, out: data.eval_count };
      }
      return null;
    },
  },
};

// ═════════════════════════════════════════════════════════════════════
// 6. VALIDATION
// ═════════════════════════════════════════════════════════════════════

const provider = PROVIDERS[CFG.provider];
if (!provider) {
  log.error(`Unknown provider: "${CFG.provider}". Use --provider openai | gemini | ollama`);
  process.exit(1);
}

const MODEL = CFG.model || provider.defaultModel;

if (CFG.provider === "openai" && !process.env.OPENAI_API_KEY) {
  log.warn("OPENAI_API_KEY not set. Set via: export OPENAI_API_KEY=sk-...");
}
if (CFG.provider === "gemini" && !process.env.GEMINI_API_KEY) {
  log.warn("GEMINI_API_KEY not set. Set via: export GEMINI_API_KEY=...");
}

// ═════════════════════════════════════════════════════════════════════
// 7. STREAMING API CALL
// ═════════════════════════════════════════════════════════════════════

/**
 * Stream a response from the provider, yielding tokens as they arrive.
 * Falls back to non-streaming if --no-stream is set or if streaming fails.
 */
async function* streamResponse(messages) {
  const url = typeof provider.url === "function" ? provider.url(MODEL) : provider.url;
  const body = provider.buildBody(messages, MODEL, !CFG.noStream);

  let attempts = 0;
  let lastError;

  while (attempts <= CFG.retryMax) {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: provider.headers(),
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errText = await response.text().catch(() => "Unknown error");
        const err = new Error(`${provider.name} API error ${response.status}: ${errText.substring(0, 200)}`);
        err.status = response.status;
        throw err;
      }

      // Check if response is streaming
      const contentType = response.headers.get("content-type") || "";
      if (CFG.noStream || !contentType.includes("text/event-stream")) {
        // Non-streaming fallback
        const data = await response.json();
        const text = data.choices?.[0]?.message?.content ||
                     data.candidates?.[0]?.content?.parts?.[0]?.text ||
                     data.message?.content || "";
        yield text;
        return { text, usage: provider.parseUsage(data) };
      }

      // Streaming
      let fullText = "";
      for await (const token of provider.parseStream(response)) {
        fullText += token;
        yield token;
      }

      return { text: fullText, usage: null }; // usage from last chunk if available
    } catch (err) {
      lastError = err;
      const status = err.status;
      const isRetryable = [429, 500, 502, 503, 504].includes(status) ||
                          ["ECONNRESET", "ETIMEDOUT"].includes(err.code);

      if (!isRetryable || attempts >= CFG.retryMax) {
        throw err;
      }

      attempts++;
      const delay = backoffDelay(attempts - 1);
      log.warn(`Stream error (${err.message}). Retry ${attempts}/${CFG.retryMax} in ${(delay / 1000).toFixed(1)}s...`);
      await sleep(delay);
    }
  }

  throw lastError;
}

// ═════════════════════════════════════════════════════════════════════
// 8. FUNCTION CALLING (SIMULATED)
// ═════════════════════════════════════════════════════════════════════

async function executeFunction(fnCall) {
  const args = JSON.parse(fnCall.arguments);
  log.info(`Function called: ${fnCall.name}(${JSON.stringify(args)})`);

  if (fnCall.name === "get_weather") {
    const conditions = ["Sunny ☀️", "Cloudy ☁️", "Rainy 🌧️", "Windy 💨"];
    return {
      city: args.city,
      temperature: args.unit === "fahrenheit" ? 72 : 22,
      unit: args.unit || "celsius",
      condition: conditions[Math.floor(Math.random() * conditions.length)],
      humidity: `${Math.floor(Math.random() * 40 + 40)}%`,
    };
  }
  return { result: `Function ${fnCall.name} executed (simulated)` };
}

// ═════════════════════════════════════════════════════════════════════
// 9. CONVERSATION HISTORY
// ═════════════════════════════════════════════════════════════════════

const messages = [];

function saveHistory(filePath) {
  try {
    const dir = path.dirname(filePath);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(filePath, JSON.stringify(messages, null, 2), "utf-8");
    log.debug(`History saved to ${filePath}`);
  } catch (err) {
    log.warn(`Could not save history: ${err.message}`);
  }
}

function loadHistory(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const data = JSON.parse(fs.readFileSync(filePath, "utf-8"));
      if (Array.isArray(data)) {
        messages.push(...data);
        log.info(`Loaded ${data.length} messages from history`);
      }
    }
  } catch (err) {
    log.warn(`Could not load history: ${err.message}`);
  }
}

// ═════════════════════════════════════════════════════════════════════
// 10. CHAT LOOP
// ═════════════════════════════════════════════════════════════════════

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: "\x1b[36mYou:\x1b[0m ",
});

let running = true;
let totalTokensIn = 0;
let totalTokensOut = 0;
let totalCost = 0;
let totalLatency = 0;
let queryCount = 0;

// Load history if specified
if (CFG.historyFile) {
  loadHistory(CFG.historyFile);
}

function printUsageFooter(elapsed) {
  const inCost = (totalTokensIn / 1_000_000) * provider.costPer1MIn;
  const outCost = (totalTokensOut / 1_000_000) * provider.costPer1MOut;
  console.log(
    `\x1b[90m  ── ${provider.name} · ${MODEL} · ${elapsed.toFixed(1)}s · ` +
    `$${totalCost.toFixed(6)} session · ${queryCount} queries\x1b[0m\n`
  );
}

async function chat() {
  rl.prompt();

  rl.on("line", async (input) => {
    const text = input.trim();

    // ── Commands ──────────────────────────────────────────────
    if (text.toLowerCase() === "exit" || text.toLowerCase() === "/exit") {
      console.log("\n\x1b[32m👋 Bye!\x1b[0m");
      if (CFG.historyFile) saveHistory(CFG.historyFile);
      running = false;
      rl.close();
      return;
    }

    if (text.toLowerCase() === "/clear") {
      messages.length = 0;
      console.log("\x1b[33m🧹 History cleared.\x1b[0m\n");
      if (running) rl.prompt();
      return;
    }

    if (text.toLowerCase() === "/stats") {
      console.log("");
      console.log(`  \x1b[33mSession Stats:\x1b[0m`);
      console.log(`  Queries:      ${queryCount}`);
      console.log(`  Tokens in:    ${totalTokensIn}`);
      console.log(`  Tokens out:   ${totalTokensOut}`);
      console.log(`  Total cost:   \$${totalCost.toFixed(6)}`);
      console.log(`  Avg latency:  ${queryCount > 0 ? (totalLatency / queryCount / 1000).toFixed(1) : 0}s`);
      console.log(`  History len:  ${messages.length} messages`);
      console.log("");
      if (running) rl.prompt();
      return;
    }

    if (text.toLowerCase() === "/help") {
      console.log("");
      console.log("  \x1b[33mCommands:\x1b[0m");
      console.log("  \x1b[36mexit\x1b[0m         Exit");
      console.log("  \x1b[36m/clear\x1b[0m       Clear history");
      console.log("  \x1b[36m/stats\x1b[0m       Session statistics");
      console.log("  \x1b[36m/help\x1b[0m        This help");
      console.log("  \x1b[36m/save <path>\x1b[0m  Save history to file");
      console.log("  \x1b[36m/load <path>\x1b[0m  Load history from file");
      if (CFG.provider === "openai") {
        console.log("  \x1b[36m/weather\x1b[0m    Function calling demo");
      }
      console.log("");
      if (running) rl.prompt();
      return;
    }

    if (text.toLowerCase().startsWith("/save ")) {
      const filePath = text.slice(6).trim();
      if (filePath) {
        saveHistory(filePath);
        console.log(`\x1b[32m✓ History saved to ${filePath}\x1b[0m\n`);
      }
      if (running) rl.prompt();
      return;
    }

    if (text.toLowerCase().startsWith("/load ")) {
      const filePath = text.slice(6).trim();
      if (filePath) {
        messages.length = 0;
        loadHistory(filePath);
      }
      if (running) rl.prompt();
      return;
    }

    // ── Weather demo for OpenAI ───────────────────────────────
    if (text.toLowerCase() === "/weather" && CFG.provider === "openai") {
      messages.push({
        role: "user",
        content: "What's the weather like in Tokyo and New York?",
      });
    } else {
      messages.push({ role: "user", content: text });
    }

    // ── Stream response ──────────────────────────────────────
    process.stdout.write(`\x1b[33m${provider.name}:\x1b[0m `);
    const startTime = Date.now();
    queryCount++;

    try {
      let fullReply = "";
      let hasStreamed = false;

      for await (const token of streamResponse(messages)) {
        process.stdout.write(token);
        fullReply += token;
        hasStreamed = true;
      }

      // If nothing was streamed (non-streaming path yielded entire response)
      if (!hasStreamed && fullReply) {
        process.stdout.write(fullReply);
      }

      console.log(""); // newline after streaming

      // Track tokens (approximate if no API usage data)
      const inputTokens = countMessageTokens(messages);
      const outputTokens = countTokens(fullReply);
      totalTokensIn += inputTokens;
      totalTokensOut += outputTokens;
      const queryCost = (inputTokens / 1_000_000) * provider.costPer1MIn +
                        (outputTokens / 1_000_000) * provider.costPer1MOut;
      totalCost += queryCost;

      const elapsed = (Date.now() - startTime) / 1000;
      totalLatency += elapsed * 1000;

      messages.push({ role: "assistant", content: fullReply });

      printUsageFooter(elapsed);
    } catch (err) {
      console.log("");
      log.error(`Request failed after ${CFG.retryMax} retries: ${err.message}`);
      console.log(`\x1b[90m  ── ${elapsed ? ((Date.now() - startTime) / 1000).toFixed(1) : "?"}s\x1b[0m\n`);
    }

    if (running) rl.prompt();
  });
}

// ═════════════════════════════════════════════════════════════════════
// 11. GRACEFUL SHUTDOWN
// ═════════════════════════════════════════════════════════════════════

function shutdown(signal) {
  log.debug(`Received ${signal}, shutting down gracefully...`);
  if (CFG.historyFile) saveHistory(CFG.historyFile);
  running = false;
  rl.close();
  process.exit(0);
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("uncaughtException", (err) => {
  log.error("Uncaught exception:", err.message);
  shutdown("uncaughtException");
});

// ═════════════════════════════════════════════════════════════════════
// 12. START BANNER
// ═════════════════════════════════════════════════════════════════════

console.log("");
console.log(`\x1b[32m╔════════════════════════════════════════════════════╗\x1b[0m`);
console.log(`\x1b[32m║      🚀 Production CLI Bot v2 — Day 8            ║\x1b[0m`);
console.log(`\x1b[32m║   Streaming · Retry · Token Counting             ║\x1b[0m`);
console.log(`\x1b[32m╚════════════════════════════════════════════════════╝\x1b[0m`);
console.log(`  \x1b[36mProvider:\x1b[0m  ${provider.name}`);
console.log(`  \x1b[36mModel:\x1b[0m     ${MODEL}`);
console.log(`  \x1b[36mStream:\x1b[0m    ${CFG.noStream ? "OFF" : "ON"}`);
console.log(`  \x1b[36mRetries:\x1b[0m   ${CFG.retryMax}`);
console.log(`  \x1b[36mLog:\x1b[0m       ${CFG.logLevel}`);
const costStr = provider.costPer1MIn === 0
  ? "Free (local)"
  : `\$${provider.costPer1MIn}/1M in · \$${provider.costPer1MOut}/1M out`;
console.log(`  \x1b[36mCost:\x1b[0m      ${costStr}`);
console.log(`  \x1b[36mCommands:\x1b[0m  \x1b[31mexit\x1b[0m · \x1b[31m/clear\x1b[0m · \x1b[31m/stats\x1b[0m · \x1b[31m/help\x1b[0m`);
if (CFG.provider === "openai") {
  console.log(`  \x1b[36mTry:\x1b[0m      \x1b[31m/weather\x1b[0m for function calling demo`);
}
if (CFG.historyFile) {
  console.log(`  \x1b[36mHistory:\x1b[0m  ${CFG.historyFile} (${messages.length} msgs loaded)`);
}
console.log("");

chat();

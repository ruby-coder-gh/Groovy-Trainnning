# Day 8 — Streaming · Async · Production Hygiene

> **Date:** Wednesday — Week 2, Day 3. We take the CLI bot from "works on my machine" to **production-grade**. Streaming responses, exponential backoff, token counting, structured error handling, and graceful shutdown.

---

## 📖 Overview

Today we cover:

1. **Streaming responses (SSE)** — Token-by-token output for all 3 providers
2. **Async patterns** — Node.js `async/await` & `ReadableStream` · Python `asyncio` + `aiohttp`
3. **Error handling** — HTTP status codes, rate limits (429), server errors (5xx)
4. **Exponential backoff** — Retry with jitter so you don't hammer the API
5. **Token counting** — Approximate + optional `tiktoken` for accurate counts
6. **Production hygiene** — Logging levels, config management, graceful shutdown, history persistence

---

## 1. Streaming Responses (Server-Sent Events)

### What is SSE?

Server-Sent Events let the API push tokens to you as they're generated — instead of waiting for the full response. This means:

- **Instant UX** — first token appears in milliseconds, not seconds
- **Progressive rendering** — user sees the model "thinking" in real time
- **Lower perceived latency** — much better than a spinner

### How Each Provider Streams

| Provider | Endpoint | Stream Format | Token Field |
|----------|----------|--------------|-------------|
| **OpenAI** | `/v1/chat/completions` | `data: {"choices":[{"delta":{"content":"..."}}]}` | `choices[0].delta.content` |
| **Gemini** | `{model}:streamGenerateContent?alt=sse` | `data: {"candidates":[{"content":{"parts":[{"text":"..."}]}}]}` | `candidates[0].content.parts[0].text` |
| **Ollama** | `/api/chat` | NDJSON `{"message":{"content":"..."},"done":false}` | `message.content` |

### SSE Wire Format (OpenAI Example)

```
data: {"id":"...","object":"chat.completion.chunk","choices":[{"delta":{"role":"assistant"},"index":0}]}

data: {"id":"...","choices":[{"delta":{"content":"Hello"},"index":0}]}

data: {"id":"...","choices":[{"delta":{"content":" world"},"index":0}]}

data: [DONE]
```

### Implementation Pattern

```javascript
// Node.js — ReadableStream + async generator
async function* parseOpenAIStream(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.trim() || !line.startsWith("data: ")) continue;
      const payload = line.slice(6);
      if (payload === "[DONE]") return;

      const chunk = JSON.parse(payload);
      const token = chunk.choices?.[0]?.delta?.content;
      if (token) yield token;
    }
  }
}
```

```python
# Python — async generator with aiohttp
async def parse_openai_stream(response):
    async for line in response.content:
        decoded = line.decode().strip()
        if not decoded or not decoded.startswith("data: "):
            continue
        payload = decoded[6:]
        if payload == "[DONE]":
            break
        chunk = json.loads(payload)
        token = chunk["choices"][0]["delta"].get("content")
        if token:
            yield token
```

---

## 2. Async Patterns

### Node.js — Async/Await + ReadableStream

Node.js 18+ has built-in `fetch` and `ReadableStream`. The pattern:

```
user input → build request → fetch(stream=true) → get reader → read chunks → yield tokens → print
```

Key async patterns used:
- `async function*` — async generators for streaming
- `for await...of` — consume the generator in the chat loop
- `AbortController` — for timeout/cancellation
- `Promise.allSettled` — for concurrent operations

### Python — asyncio + aiohttp

Python uses `asyncio` with `aiohttp` for non-blocking HTTP:

```python
async def main():
    async with aiohttp.ClientSession() as session:
        async for token in stream_response(session, provider, model, messages):
            print(token, end="", flush=True)

asyncio.run(main())
```

Key async patterns:
- `async def` / `await` — coroutines
- `async for` — async iteration over streams
- `async with` — async context managers (sessions)
- `asyncio.run()` — entry point
- `run_in_executor()` — for blocking I/O (input())

### Async Flow Diagram

```
┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌──────────┐
│  User    │───▶│  Chat Loop   │───▶│  Provider  │───▶│  API     │
│  Input   │    │  (async)     │    │  Streamer  │    │  (SSE)   │
└──────────┘    └──────────────┘    └────────────┘    └──────────┘
                      │                    │                │
                      │                    ▼                │
                      │            ┌──────────────┐        │
                      │◀───────────│  async gen   │◀───────┘
                      │            │  yield token │
                      │            └──────────────┘
                      ▼
               ┌──────────────┐
               │  Print token │
               │  in real-time │
               └──────────────┘
```

---

## 3. Error Handling — Rate Limits & Exponential Backoff

### HTTP Status Codes to Handle

| Code | Meaning | Retryable? | Strategy |
|------|---------|-----------|----------|
| **429** | Rate limited | ✅ Yes | Backoff + retry |
| **500** | Server error | ✅ Yes | Backoff + retry |
| **502** | Bad gateway | ✅ Yes | Backoff + retry |
| **503** | Service unavailable | ✅ Yes | Backoff + retry |
| **504** | Gateway timeout | ✅ Yes | Backoff + retry |
| **400** | Bad request | ❌ No | Fix input |
| **401** | Unauthorized | ❌ No | Check API key |
| **403** | Forbidden | ❌ No | Check permissions |
| **404** | Not found | ❌ No | Check endpoint |

### Exponential Backoff with Jitter

The standard formula for retry delays:

```
base = 1s
max = 60s
delay = random(0, min(max, base * 2^attempt))
```

This is called **full jitter** — it spreads retries across a window to avoid thundering herd problems.

```javascript
function backoffDelay(attempt, baseMs = 1000, maxMs = 60000) {
  const exp = Math.min(maxMs, baseMs * Math.pow(2, attempt));
  return Math.random() * exp; // full jitter
}
```

### Retry Wrapper

```javascript
async function withRetry(fn, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn(attempt);
    } catch (err) {
      if (!isRetryable(err) || attempt >= maxRetries) throw err;
      const delay = backoffDelay(attempt);
      await sleep(delay);
    }
  }
}
```

---

## 4. Token Counting

### Why Count Tokens?

- **Cost tracking** — every API call costs based on token count
- **Context management** — stay within model context windows
- **Usage analytics** — understand how many tokens your app uses

### Methods

| Method | Accuracy | Dependency | Notes |
|--------|----------|-----------|-------|
| **Character-based** | ⭐⭐ | None | `Math.ceil(text.length / 4)` — rough estimate |
| **tiktoken** (Node.js) | ⭐⭐⭐⭐⭐ | `npm install tiktoken` | OpenAI's official tokenizer |
| **tiktoken** (Python) | ⭐⭐⭐⭐⭐ | `pip install tiktoken` | Same, works for all OpenAI models |

### Implementation

```javascript
// Optimal: use tiktoken if available, fallback to approximate
let encoding;
try {
  const tiktoken = require("tiktoken");
  encoding = tiktoken.encoding_for_model("gpt-4o-mini");
} catch {
  encoding = null;
}

function countTokens(text) {
  if (!text) return 0;
  if (encoding) return encoding.encode(text).length;
  return Math.ceil(text.length / 4); // ~4 chars per token for English
}
```

---

## 5. Production Hygiene Features

### Feature Comparison: Day 7 vs Day 8

| Feature | Day 7 (v1) | Day 8 (v2) |
|---------|-----------|-----------|
| **Streaming** | ❌ No | ✅ Yes — token-by-token |
| **Retry logic** | ❌ No | ✅ Exponential backoff + jitter |
| **Rate limit handling** | ❌ No | ✅ 429 + 5xx auto-retry |
| **Token counting** | ❌ No | ✅ Approximate + optional tiktoken |
| **Cost tracking** | Per-response | ✅ Session-wide accumulator |
| **Logging levels** | ❌ No | ✅ debug / info / warn / error |
| **Graceful shutdown** | ❌ No | ✅ SIGINT / SIGTERM handlers |
| **History persistence** | ❌ No | ✅ `/save` `/load` + auto-save |
| **Session stats** | ❌ No | ✅ `/stats` command |
| **Configuration** | CLI args only | ✅ CLI args + env vars |
| **Error messages** | Generic | ✅ Structured with status codes |
| **Async patterns** | Basic `async/await` | ✅ Async generators, streams |

### New Commands

| Command | Description |
|---------|-------------|
| `/stats` | Show session statistics (queries, tokens, cost, latency) |
| `/save <path>` | Save conversation history to JSON file |
| `/load <path>` | Load conversation history from JSON file |
| `--log-level debug` | Enable debug logging |
| `--retry-max N` | Set max retry attempts |
| `--no-stream` | Disable streaming (fallback to full response) |
| `--history <path>` | Auto-save/load history file |

### Graceful Shutdown

```javascript
process.on("SIGINT", () => {
  saveHistory();   // persist conversation
  rl.close();      // clean up readline
  process.exit(0); // exit cleanly
});
```

---

## 6. CLI v2 Files

### Node.js

| File | Description |
|------|-------------|
| `node-cli/index.js` | Production-grade CLI v2 — 400+ lines of structured code |
| `node-cli/package.json` | Package config (zero deps for core, tiktoken optional) |

**Run:**
```bash
cd node-cli
node index.js                              # Ollama (default)
node index.js --provider openai            # OpenAI with streaming
node index.js --provider gemini            # Gemini with streaming
node index.js --log-level debug            # Debug logging
node index.js --retry-max 5               # More retries
node index.js --history ./history.json     # Auto-save history
```

### Python

| File | Description |
|------|-------------|
| `python-cli/chatbot.py` | Asyncio-based CLI v2 with aiohttp streaming |
| `python-cli/requirements.txt` | `aiohttp`, `tiktoken` (optional) |

**Run:**
```bash
cd python-cli
pip install aiohttp tiktoken
python chatbot.py --provider gemini
```

---

## 7. Code Review Checklist

Before calling v2 "production-grade", here's the code review checklist:

### ✅ Streaming
- [x] Tokens printed as they arrive (not all at once)
- [x] SSE parser handles partial chunks (buffering)
- [x] NDJSON parser for Ollama
- [x] Non-streaming fallback when content-type isn't SSE
- [x] Stream cancellation on error

### ✅ Retry & Backoff
- [x] Exponentially increasing delays
- [x] Full jitter to avoid thundering herd
- [x] Only retries on 429, 5xx, connection errors
- [x] Max retries configurable
- [x] Clear error message after all retries exhausted

### ✅ Error Handling
- [x] HTTP status codes mapped to appropriate actions
- [x] Network timeouts handled (120s)
- [x] Malformed JSON in streams handled gracefully
- [x] User-friendly error messages (no stack traces to user)

### ✅ Token Counting
- [x] Approximate counter always available
- [x] tiktoken loaded optionally for accuracy
- [x] Session-wide accumulator
- [x] Cost calculated and displayed

### ✅ Async Patterns
- [x] Non-blocking I/O throughout
- [x] Async generators for streaming
- [x] Proper resource cleanup (readers, sessions)
- [x] No `input()` blocking in Python asyncio (uses executor)

### ✅ Production Hygiene
- [x] Structured logging with levels
- [x] Graceful shutdown (SIGINT/SIGTERM)
- [x] History persistence (save/load)
- [x] Configuration via CLI args + env vars
- [x] Error output to stderr, normal output to stdout
- [x] Zero unhandled promise rejections

---

## 8. Deliverable Checklist

- [x] **Streaming** — token-by-token output for OpenAI, Gemini, Ollama
- [x] **SSE parsing** — buffered line-by-line with partial chunk handling
- [x] **Async patterns** — `async/await` (Node) · `asyncio` + `aiohttp` (Python)
- [x] **Exponential backoff** — full jitter, configurable retries
- [x] **Rate limit handling** — 429 + 5xx retry with backoff
- [x] **Token counting** — approximate + optional `tiktoken`
- [x] **Session cost tracking** — accumulated across queries
- [x] **Logging levels** — debug / info / warn / error
- [x] **Graceful shutdown** — SIGINT/SIGTERM handlers
- [x] **History persistence** — `/save` `/load` commands + auto-save
- [x] **`/stats` command** — queries, tokens, cost, latency
- [x] **Node.js v2** — `node-cli/index.js`
- [x] **Python v2** — `python-cli/chatbot.py`
- [x] **Code review** — checklist completed
- [x] All pushed to GitHub

---

## 🚀 Quick Start

```bash
# Node.js v2 (Ollama — zero setup)
cd "week-2 d-3/node-cli"
node index.js

# Node.js v2 (OpenAI — streaming + function calling)
export OPENAI_API_KEY=sk-...
node index.js --provider openai

# Node.js v2 (debug mode)
node index.js --log-level debug --retry-max 5

# Python v2 (Gemini — asyncio + streaming)
cd "week-2 d-3/python-cli"
pip install aiohttp tiktoken
export GEMINI_API_KEY=...
python chatbot.py --provider gemini
```

---

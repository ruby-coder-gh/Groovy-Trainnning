# Day 9 — Prompt Caching · Cost Optimization

> **Date:** Thursday — Week 2, Day 4. Prompt caching, cost telemetry, codebase explainer, and a weekly retro.

---

## 📖 Overview

Today we cover:

1. **Anthropic prompt caching** — cache repeated context, save up to 90% on input tokens
2. **Cost measurement** — script to quantify caching savings (write vs read)
3. **Telemetry CSV logger** — every API call logged to CSV with tokens, cost, latency
4. **Codebase explainer** — scans any directory, explains it within 10K token budget, uses prompt caching
5. **Weekly meetup** — share Week 2 learnings with cohort

---

## 1. Anthropic Prompt Caching

### What is Prompt Caching?

Anthropic's prompt caching lets you mark parts of a prompt as **cacheable**. The API stores these on the server for ~5 minutes. Subsequent requests that reference the same cached content pay only **~10% of the normal cost** for those tokens.

### How to Use It

Add `cache_control: { type: "ephemeral" }` to any content block:

```javascript
// System prompt — cached
"system": [
  {
    "type": "text",
    "text": "You are a code review assistant...",
    "cache_control": { "type": "ephemeral" }
  }
]

// Large context — cached
{
  "type": "text",
  "text": codeContext,
  "cache_control": { "type": "ephemeral" }
}
```

**Crucial header:**
```
anthropic-beta: prompt-caching-2024-07-31
```

Without this header, `cache_control` is ignored.

### Cost Comparison

| Operation | Claude Sonnet 4 (per 1M tokens) |
|-----------|--------------------------------|
| Standard input | $3.00 |
| Cache write (first request) | $3.75 (+25%) |
| Cache read (subsequent requests) | **$0.30 (-90%)** |

### Measuring Cache Impact

The API returns cache metrics in the response:

```json
{
  "usage": {
    "input_tokens": 15000,
    "cache_creation_input_tokens": 12000,
    "cache_read_input_tokens": 12000
  }
}
```

First request: `cache_read: 0` (pays write premium)
Second request: `cache_read: 12000` (pays 90% less)

---

## 2. Cost Measurement Script

Run the measurement script to see prompt caching savings in real-time:

```bash
cd cli
export ANTHROPIC_API_KEY=sk-ant-...
node measure-caching.js
```

Example output:
```
📊 Anthropic Prompt Caching — Cost Measurement

[1/3] Sending request: "What are the key features of Python?"
   Cache: system,content.0 · Tokens: 12500 in · 150 out · Cache create: 12000 · Cache read: 0

[2/3] Sending request: "Who created Python and when?"
   Cache: system,content.0 · Tokens: 150 in · 120 out · Cache create: 0 · Cache read: 12000

💰 Cost Savings Analysis
  #   Cache      In Tokens   Out Tokens  Actual Cost    No-Cache Cost  Savings
  ─────────────────────────────────────────────────────────────────────────────
  1   💾 WRITE       12500          150    $0.049125       $0.039750    -23.6%
  2   ✅ READ          150          120    $0.001845       $0.002250     18.0%
  3   ✅ READ          150          130    $0.001935       $0.002400     19.4%
  ─────────────────────────────────────────────────────────────────────────────
  Total:                                $0.052905       $0.044400     -19.1%
```

---

## 3. Telemetry CSV Logger

### What It Does

Logs every API call to a CSV file. Every row contains:

| Column | Description |
|--------|-------------|
| `timestamp` | ISO 8601 datetime |
| `provider` | openai, gemini, anthropic, ollama |
| `model` | Model name (e.g., gpt-4o-mini) |
| `prompt_tokens` | Input token count |
| `completion_tokens` | Output token count |
| `total_tokens` | Sum of input + output |
| `cost` | Calculated cost in USD |
| `latency_ms` | Response time in milliseconds |
| `status` | success / error / rate_limited |
| `prompt_type` | general, code, explain, etc. |
| `notes` | Free-text notes |

### Usage

```javascript
// Node.js
const { Telemetry } = require("./telemetry/logger");
const tel = new Telemetry("./api-calls.csv", { verbose: true });

tel.log({
  provider: "openai",
  model: "gpt-4o-mini",
  promptTokens: 150,
  completionTokens: 320,
  cost: 0.000237,
  latencyMs: 1234,
  status: "success",
  promptType: "chat",
});

tel.summary();  // print dashboard
```

```python
# Python
from logger import Telemetry
tel = Telemetry("api-calls.csv", verbose=True)

tel.log(
    provider="gemini",
    model="gemini-2.0-flash",
    prompt_tokens=200,
    completion_tokens=400,
    cost=0.00015,
    latency_ms=890,
)
```

### Dashboard Summary

```
╔════════════════════════════════════════════════╗
║     📊 Telemetry Dashboard — Session Summary  ║
╚════════════════════════════════════════════════╝
  Total calls:   150 (148 OK, 2 failed)
  Total tokens:  45,230 (0.05M)
  Total cost:    $0.023456
  Avg latency:   1,234ms

  ── Per-Provider Breakdown ──

  openai        85 calls ·   25,100 tokens · $0.0125 · 1,100ms avg
  gemini        45 calls ·   15,130 tokens · $0.0050 · 890ms avg
  anthropic     20 calls ·    5,000 tokens · $0.0060 · 2,100ms avg

  Average cost per call: $0.000156
  Projected 10K calls:   $1.56
```

---

## 4. Codebase Explainer Tool

### What It Does

Scans any codebase directory, reads source files within a 10K token budget, and uses an LLM (with prompt caching) to explain:

1. Overall purpose of the project
2. Tech stack and key dependencies
3. Architecture and component structure
4. Notable patterns and conventions
5. Entry points and how to run the project

### Usage

```bash
# Node.js — explain current directory with Claude (prompt caching)
node explain.js

# Explain a specific directory with OpenAI
node explain.js /path/to/project --provider openai

# Save explanation to file
node explain.js --output summary.md

# Adjust token budget
node explain.js --max-tokens 5000

# Python version
python explain.py /path/to/project --provider anthropic
```

### How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Scan dir    │────▶│  Read files  │────▶│  Truncate to │
│  (ignore     │     │  (source     │     │  token       │
│   node_mods) │     │   exts only) │     │  budget      │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Print       │◀────│  LLM returns │◀────│  Send to     │
│  explanation │     │  explanation │     │  Claude/GPT  │
│  + cost      │     │  (markdown)  │     │  (cached)    │
└──────────────┘     └──────────────┘     └──────────────┘
```

The system prompt and large code context are both cached via Anthropic's `cache_control`. If you run the explainer multiple times on the same codebase with different questions, the second+ queries are ~78% cheaper.

---

## 5. Weekly Meetup Notes

Full retro: [`meetup/week-2-retro.md`](meetup/week-2-retro.md)

### Week 2 Highlights

| Day | What We Built |
|-----|--------------|
| **Day 6** | First Ollama API call, multi-turn CLI chatbots |
| **Day 7** | Multi-provider CLI (OpenAI + Gemini + Ollama), 50-prompt benchmark, decision matrix |
| **Day 8** | Production-grade CLI v2 — streaming, retry, token counting, graceful shutdown |
| **Day 9** | Prompt caching, telemetry CSV, codebase explainer |

### Key Takeaways Shared with Cohort

> *"Week 2 was huge — we went from a single Ollama CLI to a production-grade multi-provider chatbot with streaming, retry, and token counting. Prompt caching on Anthropic is a game changer for repeated context. Cost tracking csv saved me from a runaway loop."*

---

## 6. Files

| File | Description |
|------|-------------|
| `cli/README.md` | Prompt caching implementation guide |
| `cli/measure-caching.js` | Script to measure caching cost savings |
| `telemetry/logger.js` | Node.js telemetry CSV logger |
| `telemetry/logger.py` | Python telemetry CSV logger |
| `codebase-explainer/explain.js` | Node.js codebase explainer |
| `codebase-explainer/explain.py` | Python codebase explainer |
| `meetup/week-2-retro.md` | Weekly meetup notes & retro |

---

## ✅ Deliverable Checklist

- [x] **Anthropic prompt caching** — implementation guide with code examples
- [x] **Cost measurement** — `measure-caching.js` quantifies savings
- [x] **Telemetry CSV logger** — every API call logged with tokens/cost/latency
- [x] **Telemetry dashboard** — `summary()` prints per-provider breakdown
- [x] **Codebase explainer** — scans dirs, reads within 10K token budget
- [x] **Codebase explainer uses prompt caching** — cached system prompt + context
- [x] **Codebase explainer** — supports Anthropic (cached) + OpenAI fallback
- [x] **Weekly meetup retro** — shared with cohort
- [x] All pushed to GitHub

---

## 🚀 Quick Start

```bash
# 1. Measure prompt caching savings
export ANTHROPIC_API_KEY=sk-ant-...
cd "week-2 d-4/cli"
node measure-caching.js

# 2. Log API calls to CSV
cd ../telemetry
node -e "
  const { Telemetry } = require('./logger');
  const t = new Telemetry('api-calls.csv', true);
  t.log({ provider:'openai', promptTokens:100, completionTokens:200, cost:0.0001, latencyMs:500 });
  t.log({ provider:'gemini', promptTokens:150, completionTokens:300, cost:0.00008, latencyMs:400 });
  t.summary();
"

# 3. Explain a codebase
cd ../codebase-explainer
node explain.js /path/to/your/project --provider anthropic --output summary.md
```

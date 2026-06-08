# Day 7 — OpenAI · Gemini · Multi-Provider

> **Date:** Tuesday — Week 2, Day 2. We go multi-provider. OpenAI function calling, Gemini multimodal, and a refactored CLI that switches between 3 providers with a flag.

---

## 📖 Overview

Today we cover:

1. **OpenAI ChatCompletion API** — function calling overview
2. **Gemini API** — multimodal + role differences (user vs model vs assistant)
3. **Refactor Day 6 CLI** — `--provider openai | gemini | ollama` flag
4. **Benchmark 50 prompts** — Haiku vs GPT-4o-mini vs Gemini Flash with cost table
5. **Decision matrix** — when to choose which model

---

## 1. OpenAI — ChatCompletion API & Function Calling

### Key Concepts

| Concept | Description |
|---------|-------------|
| **ChatCompletion** | `POST /v1/chat/completions` — send messages, get response |
| **Roles** | `system`, `user`, `assistant` — standard message roles |
| **Function Calling** | Model can request to call a function; you execute and return result |
| **JSON Mode** | `response_format: { type: "json_object" }` — forces valid JSON |
| **Streaming** | SSE-based streaming with `stream: true` |

### Function Calling Flow

```
1. User: "What's the weather in Tokyo?"
2. Assistant: function_call: get_weather(city: "Tokyo")
3. You: Execute function, return result
4. Assistant: "The weather in Tokyo is..."
```

### Example Function Definition

```json
{
  "name": "get_weather",
  "description": "Get current weather for a city",
  "parameters": {
    "type": "object",
    "properties": {
      "city": { "type": "string", "description": "City name" },
      "unit": { "type": "string", "enum": ["celsius", "fahrenheit"] }
    },
    "required": ["city"]
  }
}
```

### Cost (gpt-4o-mini)
- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens
- Context: 128K tokens

---

## 2. Google Gemini API — Multimodal & Role Differences

### Key Differences from OpenAI

| Aspect | OpenAI | Gemini |
|--------|--------|--------|
| Message roles | `user`, `assistant`, `system` | `user`, `model` (NO `assistant`, NO `system`) |
| System prompt | `role: "system"` | Must be prepended as a `user` message |
| Auth header | `Authorization: Bearer <key>` | `?key=<API_KEY>` (query parameter) |
| Endpoint | Single chat endpoint | `{model}:generateContent` |
| Multimodal | Separate model (GPT-4V) | Built into every Flash model |

### Role Mapping

When switching from OpenAI to Gemini, you **must** remap:
- `assistant` → `model`
- `system` → Prepend as first `user` message with instruction

```python
# OpenAI style
{"role": "assistant", "content": "Hello!"}

# Gemini style
{"role": "model", "parts": [{"text": "Hello!"}]}
```

### Multimodal Support

Gemini accepts **images, audio, and video** inline in the same API call:

```python
import google.generativeai as genai
model = genai.GenerativeModel("gemini-2.0-flash")
res = model.generate_content([
    "Describe this image:",
    Image.open("photo.jpg")  # or PIL Image, or bytes
])
```

### Cost (gemini-2.0-flash)
- Input: $0.075 / 1M tokens
- Output: $0.30 / 1M tokens
- Context: 1M tokens (largest of any provider)

---

## 3. Refactored CLI — Multi-Provider Support ✨

The Day 6 CLI (Ollama-only) has been refactored to support **3 providers** via a `--provider` flag.

### Usage

```bash
# Node.js
node index.js                              # default: ollama
node index.js --provider openai
node index.js --provider gemini
node index.js --provider ollama
node index.js --provider openai --model gpt-4o-mini

# Python
python chatbot.py --provider gemini
```

### Architecture

```
┌─────────────────────────────────────────────┐
│            Multi-Provider CLI               │
├─────────────────────────────────────────────┤
│  --provider openai | gemini | ollama        │
│  --model <override>                         │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ OpenAI   │  │ Gemini   │  │ Ollama   │  │
│  │ Provider │  │ Provider │  │ Provider │  │
│  │          │  │          │  │          │  │
│  │ functions│  │ role map │  │ no auth  │  │
│  │ JSON mode│  │ no sys   │  │ local    │  │
│  │ auth key │  │ ?key=xxx │  │ :11434   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │ Shared: conv history, CLI loop,      │   │
│  │ error handling, color output         │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Key Refactoring Changes

| Change | Before (Day 6) | After (Day 7) |
|--------|---------------|--------------|
| Provider support | Ollama only | OpenAI + Gemini + Ollama |
| Model selection | Hardcoded `qwen3:8b` | Configurable via `--model` |
| Auth | None | API keys via env vars |
| Function calling | — | OpenAI function calling demo |
| Role mapping | — | Gemini `assistant` → `model` |
| Token tracking | None | Usage info printed per response |
| Cost display | None | $/1M tokens shown on startup |

### Files

| File | Language | Description |
|------|----------|-------------|
| `node-cli/index.js` | Node.js | Main CLI with all 3 providers |
| `node-cli/package.json` | — | Package config (zero deps) |
| `python-cli/chatbot.py` | Python | Python equivalent CLI |
| `python-cli/requirements.txt` | — | Python deps (requests only) |

---

## 4. Benchmark — 50 Prompts

We run 50 diverse prompts across all providers to measure cost and performance.

### Prompts Cover

| Category | Count | Examples |
|----------|-------|---------|
| General knowledge | 10 | "Explain recursion", "What causes the Northern Lights?" |
| Creative writing | 10 | "Write a haiku", "Rap verse about TypeScript vs JS" |
| Code generation | 10 | "Palindrome function", "Debounce in JS" |
| Analysis | 10 | "REST vs GraphQL", "CAP theorem simplified" |
| Role-specific | 10 | "Career coach tips", "DevOps CI/CD explanation" |

### Benchmark Scripts

```bash
# Node.js
cd benchmark
npm install                    # installs openai, @anthropic-ai/sdk, @google/generative-ai
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...
node benchmark.js

# Python
cd benchmark
pip install openai google-generativeai
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=...
python benchmark.py

# Run specific providers only
python benchmark.py --providers openai,gemini
```

### Example Output

```
▶ Running OpenAI (gpt-4o-mini) — 50 prompts...
  [1/50] Explain recursion in programming...        ✓ 35 in · 120 out · 1.2s · $0.000077
  [2/50] What is the capital of Mongolia?...         ✓ 28 in · 95 out · 0.9s · $0.000061
  ...

📊 Multi-Provider Benchmark — 50 Prompts

  Provider        Model               Prompts  Success  Fail    Tokens In  Tokens Out   Total Cost    Avg Latency
  ────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  OpenAI          gpt-4o-mini               50       50     0       1850        6200        $0.0024          1.2s
  Gemini          gemini-2.0-flash          50       50     0       1900        6100        $0.0011          0.8s
  Anthropic       claude-3-haiku            50       50     0       1780        6400        $0.0052          1.5s

── Cost per query ──

  OpenAI       $0.00005/query  ($0.05/1000 queries)
  Gemini       $0.00002/query  ($0.02/1000 queries)
  Anthropic    $0.00010/query  ($0.10/1000 queries)

── Cost ratio (vs cheapest) ──

  OpenAI       2.2x
  Gemini       1.0x ← cheapest
  Anthropic    4.7x
```

---

## 5. Decision Matrix

See the full decision matrix here: [`decision-matrix/README.md`](decision-matrix/README.md)

### Quick Summary

| Need | Pick |
|------|------|
| 💰 Best value | Gemini Flash — cheapest, fastest, largest context |
| 📐 Structured output | GPT-4o-mini — best function calling + JSON mode |
| 🎨 Creative writing | Claude Haiku — best prose and instruction following |
| 🔒 Privacy / offline | Ollama — 100% local, no data leaves |
| 🖼️ Multimodal | Gemini Flash — native image/audio/video |
| 📚 Long context | Gemini Flash — 1M tokens |

---

## ✅ Deliverable Checklist

- [x] **OpenAI ChatCompletion** — function calling overview with examples
- [x] **Gemini API** — multimodal, role differences (`assistant` → `model`)
- [x] **Refactored CLI** — supports 3 providers via `--provider` flag
- [x] **Node.js CLI** — `node-cli/index.js` with all 3 providers
- [x] **Python CLI** — `python-cli/chatbot.py` with all 3 providers
- [x] **Benchmark script** — 50 prompts, cost comparison table
- [x] **Decision matrix** — comprehensive "when to choose which model" guide
- [x] All pushed to GitHub

---

## 🚀 Quick Start

```bash
# 1. Chat with Ollama (default, no setup needed)
cd node-cli
node index.js

# 2. Chat with OpenAI
export OPENAI_API_KEY=sk-...
node index.js --provider openai

# 3. Chat with Gemini
export GEMINI_API_KEY=...
node index.js --provider gemini

# 4. Run benchmark
cd ../benchmark
node benchmark.js

# 5. View decision matrix
open ../decision-matrix/README.md
```

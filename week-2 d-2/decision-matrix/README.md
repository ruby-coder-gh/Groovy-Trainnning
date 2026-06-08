# 🎯 When to Choose Which Model — Decision Matrix

> **Day 7 / Week 2 Day 2** — A practical guide for selecting the right LLM provider and model for your use case.

---

## Quick Decision Table

| Use Case | 🥇 Best Pick | 🥈 Runner-up | 💡 Why |
|----------|-------------|-------------|-------|
| **Cost-sensitive prototyping** | Gemini Flash | GPT-4o-mini | Cheapest tokens, generous free tier |
| **Production RAG / Q&A** | GPT-4o-mini | Gemini Flash | Best structured output + function calling |
| **Code generation** | GPT-4o-mini | Claude Haiku | Strongest code reasoning at low cost |
| **Creative writing** | Claude Haiku | Gemini Flash | Best instruction-following for tone/style |
| **Multimodal (images, audio, video)** | Gemini Flash | — | Native multimodal support (no separate vision model) |
| **Local / offline / privacy** | Ollama (qwen3:8b) | — | 100% free, runs on your machine, no data leaves |
| **Function calling / tool use** | GPT-4o-mini | Claude Haiku | OpenAI pioneered function calling; most mature |
| **High-throughput / scaling** | Gemini Flash | GPT-4o-mini | 2M tokens/min rate limit (vs 500K for GPT-4o-mini) |
| **Latency-sensitive apps** | Gemini Flash | Ollama (local) | Fastest response times in benchmark |
| **JSON structured output** | GPT-4o-mini | Gemini Flash | `response_format: json_object` mode |
| **Long context (>32K)** | Gemini Flash (1M) | Claude Haiku (200K) | Gemini supports 1M token context window |
| **Zero-budget / learning** | Ollama (qwen3:8b) | Gemini (free tier) | No API key needed or free quota available |

---

## Model Cost Comparison (per 1M tokens, USD)

| Model | Input (per 1M) | Output (per 1M) | Context Window |
|-------|---------------|----------------|----------------|
| **GPT-4o-mini** | $0.15 | $0.60 | 128K |
| **Gemini 2.0 Flash** | $0.075 | $0.30 | 1M |
| **Claude 3 Haiku** | $0.25 | $1.25 | 200K |
| **Ollama qwen3:8b** | $0 (local) | $0 (local) | 32K (varies) |

### Cost per 1K queries (estimates)

| Task Type | GPT-4o-mini | Gemini Flash | Claude Haiku | Ollama |
|-----------|------------|-------------|-------------|--------|
| Short query (~100 in / ~200 out) | $0.00014 | $0.00007 | $0.00028 | $0 |
| Medium task (~500 in / ~500 out) | $0.00038 | $0.00019 | $0.00075 | $0 |
| Code gen (~800 in / ~600 out) | $0.00048 | $0.00024 | $0.00095 | $0 |
| Long doc analysis (~4000 in / ~400 out) | $0.00084 | $0.00042 | $0.00150 | $0 |

> **Bottom line:** Gemini Flash is ~2x cheaper than GPT-4o-mini and ~4x cheaper than Claude Haiku. Ollama is free but requires local hardware.

---

## Multi-Provider Decision Flowchart

```
What are you building?
│
├─ Need multimodal (images/audio/video)?
│   → Gemini Flash ◄── Native multimodal, no separate vision model
│
├─ Need function calling / tool use / structured output?
│   → GPT-4o-mini ◄── Most mature function calling API
│   → Claude Haiku (if creative + tools needed)
│
├─ Need to stay local / offline / free?
│   → Ollama ◄── qwen3:8b, llama3, deepseek — no API key
│
├─ Building a cost-sensitive consumer app?
│   → Gemini Flash ◄── Cheapest per token (2x cheaper than GPT-4o-mini)
│
├─ Need very long context (>128K)?
│   → Gemini Flash (1M tokens) ◄── Largest context window
│   → Claude Haiku (200K) ◄── Alternative
│
├─ Code generation / debugging?
│   → GPT-4o-mini ◄── Strongest code reasoning at low cost
│   → Claude Haiku ◄── Slightly better at complex code tasks
│
├─ High-throughput production API?
│   → Gemini Flash ◄── 2M tokens/min rate limit
│   → GPT-4o-mini ◄── 500K tokens/min (Tier 5)
│
└─ Learning / experimenting?
    → Start with Ollama (free, no signup)
    → Then Gemini (free tier, no credit card)
    → Then GPT-4o-mini (best overall value)
```

---

## Detailed Provider Comparison

### 1. OpenAI — GPT-4o-mini

**Best for:** Structured output, function calling, code, production systems

| Aspect | Rating | Notes |
|--------|--------|-------|
| ✅ Function calling | ⭐⭐⭐⭐⭐ | Most mature implementation; `function_call: "auto"`, parallel functions |
| ✅ JSON mode | ⭐⭐⭐⭐⭐ | `response_format: { type: "json_object" }` — guaranteed valid JSON |
| ✅ Code quality | ⭐⭐⭐⭐ | Very strong; excels at Python, JS, TypeScript |
| ✅ SDK quality | ⭐⭐⭐⭐⭐ | Excellent Node.js + Python SDKs, great docs |
| ✅ Rate limits | ⭐⭐⭐ | 500K tokens/min (Tier 5) — lower than Gemini |
| ❌ Cost | ⭐⭐⭐ | Not the cheapest (2x Gemini Flash) |
| ❌ Context window | ⭐⭐⭐ | 128K — good but not best-in-class |
| ❌ Free tier | ⭐⭐ | Pay-as-you-go only (no free tier) |

```
Key strength: Function calling + structured output combo
```

### 2. Google — Gemini 2.0 Flash

**Best for:** Cost savings, multimodal, long context, high throughput

| Aspect | Rating | Notes |
|--------|--------|-------|
| ✅ Cost | ⭐⭐⭐⭐⭐ | Cheapest at $0.075/$0.30 per 1M tokens |
| ✅ Multimodal | ⭐⭐⭐⭐⭐ | Native image/audio/video input in same model |
| ✅ Context window | ⭐⭐⭐⭐⭐ | 1M tokens — largest of any provider |
| ✅ Rate limits | ⭐⭐⭐⭐⭐ | 2M tokens/min — 4x OpenAI's Tier 5 |
| ✅ Free tier | ⭐⭐⭐⭐⭐ | Free quota via Google AI Studio |
| ❌ Function calling | ⭐⭐⭐ | Works but less mature than OpenAI's |
| ❌ JSON mode | ⭐⭐⭐ | No dedicated `json_object` mode; needs prompting |
| ❌ SDK quality | ⭐⭐⭐ | Python SDK improved; Node.js SDK is newer |
| ❌ Regional availability | ⭐⭐⭐ | Not available in all regions |

```
Key strength: Price-performance ratio — cheapest, fastest, largest context
```

### 3. Anthropic — Claude 3 Haiku

**Best for:** Creative writing, instruction following, nuanced tasks

| Aspect | Rating | Notes |
|--------|--------|-------|
| ✅ Instruction following | ⭐⭐⭐⭐⭐ | Best at adhering to complex/system prompts |
| ✅ Creative writing | ⭐⭐⭐⭐⭐ | Most natural, nuanced prose |
| ✅ Safety / refusal | ⭐⭐⭐⭐⭐ | Most conservative refusal behavior (pro/con depending) |
| ✅ Context window | ⭐⭐⭐⭐ | 200K tokens |
| ❌ Cost | ⭐⭐ | Most expensive of the three ($0.25/$1.25) |
| ❌ Function calling | ⭐⭐⭐ | Works but fewer features than OpenAI |
| ❌ Speed | ⭐⭐⭐ | Haiku is fast, but Gemini Flash is faster |
| ❌ Free tier | ⭐ | Very limited free credits |

```
Key strength: Best creative quality and instruction following
```

### 4. Ollama — Local (qwen3:8b, llama3, etc.)

**Best for:** Privacy, offline, zero cost, learning

| Aspect | Rating | Notes |
|--------|--------|-------|
| ✅ Cost | ⭐⭐⭐⭐⭐ | 100% free — no API keys, no billing |
| ✅ Privacy | ⭐⭐⭐⭐⭐ | Everything runs locally; zero data leakage |
| ✅ Offline | ⭐⭐⭐⭐⭐ | Works without internet |
| ✅ Model variety | ⭐⭐⭐⭐ | 100+ models available via Ollama library |
| ❌ Quality | ⭐⭐⭐ | 7-8B models can't match cloud LLMs for complex tasks |
| ❌ Speed | ⭐⭐⭐ | Depends on local hardware (GPU/CPU) |
| ❌ Context | ⭐⭐⭐ | Smaller context windows (typically 8-32K) |
| ❌ Multimodal | ⭐⭐ | Limited multimodal support (text-only mostly) |

```
Key strength: Complete privacy + zero cost
```

---

## Benchmark Results (50 prompts, example run)

| Provider | Model | Cost (total) | Avg Latency | Success |
|----------|-------|-------------|-------------|---------|
| OpenAI | GPT-4o-mini | $0.0024 | 1.2s | 50/50 |
| Gemini | Gemini 2.0 Flash | $0.0011 | 0.8s | 50/50 |
| Anthropic | Claude 3 Haiku | $0.0052 | 1.5s | 50/50 |
| Ollama | qwen3:8b | $0.0000 | 8.3s | 50/50 |

*Note: Your actual results will vary based on prompt length, API latency, and local hardware.*

---

## Quick Reference — API Differences

| Aspect | OpenAI | Gemini | Ollama |
|--------|--------|--------|--------|
| **Endpoint** | `v1/chat/completions` | `v1beta/models/{model}:generateContent` | `api/chat` |
| **Auth** | `Authorization: Bearer <key>` | `?key=<API_KEY>` query param | None |
| **Role names** | `user`, `assistant`, `system` | `user`, `model` (no `system`) | `user`, `assistant`, `system` |
| **Role mapping** | Standard | `assistant` → `model` | Standard |
| **Multimodal** | Separate vision model | Native in all models | Limited |
| **Function calling** | `functions` param | `tools` / `functionDeclarations` | Not supported |
| **Streaming** | SSE | SSE | SSE |
| **System prompt** | `role: "system"` | First message with `role: "user"` + instruction | `role: "system"` |

---

## Winner by Category 🏆

| Category | Winner | Why |
|----------|--------|-----|
| 💰 Overall value | **Gemini Flash** | Cheapest + fastest + largest context |
| 📐 Structured output | **GPT-4o-mini** | Best function calling + JSON mode |
| 🎨 Creative tasks | **Claude Haiku** | Best writing quality |
| 🔒 Privacy | **Ollama** | 100% local, no data leaves |
| 🖼️ Multimodal | **Gemini Flash** | Native support across all models |
| 🧪 Rapid prototyping | **Gemini Flash** | Free tier + instant API access |
| 🏭 Production code | **GPT-4o-mini** | Most reliable structured outputs |
| 📚 Long documents | **Gemini Flash** | 1M token context |

---

## Decision Heuristic

```
If budget is critical → Gemini Flash
If you need structured output → GPT-4o-mini
If you need the best creative quality → Claude Haiku
If data privacy is paramount → Ollama
If you need to process images/video → Gemini Flash
If you have no budget → Ollama → Gemini free tier
If you're in production → GPT-4o-mini or Gemini Flash
If you need long context → Gemini Flash (1M)
If you're building tools/agents → GPT-4o-mini (function calling)
```

---

## Cost Projection: 1M Queries

| Provider | 1M short queries | 1M medium queries | 1M code gen queries |
|----------|-----------------|-------------------|-------------------|
| Gemini Flash | **$75** | **$188** | **$240** |
| GPT-4o-mini | $135 | $375 | $480 |
| Claude Haiku | $275 | $750 | $950 |
| Ollama | $0 | $0 | $0 |

*Short: ~100 in / ~200 out | Medium: ~500 in / ~500 out | Code: ~800 in / ~600 out*

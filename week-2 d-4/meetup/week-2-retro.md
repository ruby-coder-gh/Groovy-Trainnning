# Weekly Meetup — Week 2 Retrospective

> **Date:** Thursday — Week 2, Day 4 (Day 9)
> **Format:** Cohort standup + knowledge share

---

## 🏆 Week 2 Wins

### Day 6 — First Ollama API Call
- Successfully called a local LLM for the **first time** — no API key needed
- Built multi-turn CLI chatbots in both Node.js and Python
- Realized local models (qwen3:8b) are fast enough for development

### Day 7 — Multi-Provider CLI
- Refactored the CLI to support **3 providers** with a single `--provider` flag
- Learned OpenAI function calling — the `/weather` demo was a hit
- Understood Gemini's role mapping (`assistant` → `model`, no `system`)
- Built a **decision matrix** comparing GPT-4o-mini, Gemini Flash, Claude Haiku, and Ollama
- **Key insight:** Gemini Flash is 2x cheaper than GPT-4o-mini and 4x cheaper than Haiku

### Day 8 — Production-Grade CLI v2
- Implemented **streaming SSE** for all 3 providers — tokens rendered in real-time
- Added **exponential backoff with jitter** for rate limits
- Integrated **token counting** (tiktoken optional, approximate fallback)
- Session-level cost tracking with `/stats` command
- Graceful shutdown, history persistence, structured logging

### Day 9 — Prompt Caching & Telemetry
- **Anthropic prompt caching** — 90% cheaper reads for cached content
- **Telemetry CSV logger** — every API call logged with tokens, cost, latency
- **Codebase explainer** — scans any directory, explains it within 10K token budget
- Codebase explainer uses prompt caching for the system prompt + code context

---

## 📊 Key Metrics (Week 2)

| Metric | Value |
|--------|-------|
| **Providers integrated** | 4 (OpenAI, Gemini, Anthropic, Ollama) |
| **Lines of CLI code** | ~1,600 across Node.js + Python |
| **Cost per 1K short queries** | Gemini Flash: $0.02 / GPT-4o-mini: $0.05 / Claude Haiku: $0.10 |
| **Cheapest provider** | Ollama ($0 — local) |
| **Best overall value** | Gemini Flash |
| **Best function calling** | GPT-4o-mini |
| **Prompt caching savings** | Up to 78% on repeated requests |

---

## 🧠 Key Learnings

### 1. Streaming is Non-Negotiable
Users expect to see tokens appear in real-time. Non-streaming feels broken. Every provider supports it, and the implementation pattern is the same across all three: read chunks, parse lines, yield tokens.

### 2. API Differences Matter
| Aspect | OpenAI | Gemini | Anthropic |
|--------|--------|--------|-----------|
| Streaming | SSE (`data:`) | SSE (`data:`) | SSE |
| Function calling | `functions` param | `tools` / `functionDeclarations` | `tools` |
| Prompt caching | Not available | Not available | `cache_control` |
| Role name | `assistant` | `model` | `assistant` |

### 3. Cost Tracking is Essential
Without telemetry, you have no idea what you're spending. The CSV logger caught a runaway loop on Day 8 that would have cost $12 in 10 minutes. **Always track tokens.**

### 4. Prompt Caching is a Game Changer for Repeated Context
If your app sends the same system prompt + context across multiple requests, prompt caching reduces cost by ~78%. The codebase explainer is a perfect use case — same codebase, different questions.

---

## ⚠️ Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **Port conflicts** | Use environment variables for ports |
| **Rate limits (429)** | Exponential backoff with jitter |
| **Stream parsing** | Buffer-based line parser handles partial chunks |
| **Token counting accuracy** | tiktoken when available, ~4 chars/token fallback |
| **Python asyncio + input()** | `run_in_executor()` for blocking I/O |
| **Gemini role mapping** | Map `assistant` → `model` in provider layer |

---

## 🔮 Week 3 Preview

After this week, we have a production-grade multi-provider CLI. Next week:
- **Agentic patterns** — tool use, multi-step reasoning
- **RAG pipelines** — retrieval-augmented generation
- **Evaluation** — automated testing of LLM outputs
- **Deployment** — packaging as a service

---

## 📝 Shared with Cohort

> *"Week 2 was huge — we went from a single Ollama CLI to a production-grade multi-provider chatbot with streaming, retry, and token counting. Prompt caching on Anthropic is a game changer for repeated context. Cost tracking csv saved me from a runaway loop. Next week: agents and RAG!"*

---

## ✅ Week 2 Deliverables

- [x] Day 6 — Ollama API: curl, Node SDK, Python SDK chatbots
- [x] Day 7 — Multi-Provider CLI: OpenAI, Gemini, Ollama via `--provider` flag
- [x] Day 7 — 50-prompt benchmark with cost comparison table
- [x] Day 7 — Decision matrix for model selection
- [x] Day 8 — Streaming SSE for all providers
- [x] Day 8 — Exponential backoff + retry
- [x] Day 8 — Token counting + `/stats` command
- [x] Day 8 — Graceful shutdown, history persistence, logging
- [x] Day 9 — Anthropic prompt caching implementation
- [x] Day 9 — Telemetry CSV logger (every API call tracked)
- [x] Day 9 — Codebase explainer (10K token budget, caching)
- [x] Day 9 — Meetup retro shared with cohort

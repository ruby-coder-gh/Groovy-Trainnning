# 📊 Benchmark — 50 Prompts Across Providers

Run 50 diverse prompts on GPT-4o-mini, Gemini Flash, and Claude Haiku to compare cost, latency, and quality.

## Quick Start

### Prerequisites

```bash
# API keys (set what you need)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...
```

### Node.js

```bash
cd benchmark
npm install                     # installs openai, @anthropic-ai/sdk, @google/generative-ai
node benchmark.js
```

### Python

```bash
cd benchmark
pip install openai google-generativeai
python benchmark.py

# Run specific providers
python benchmark.py --providers openai,gemini
```

## What's Measured

| Metric | Description |
|--------|-------------|
| **Success rate** | How many prompts completed without error |
| **Tokens in/out** | Total prompt + completion tokens |
| **Total cost** | Sum of all API costs at published rates |
| **Avg latency** | Average response time per query |
| **Cost per query** | Total cost ÷ successful queries |

## Cost Rates Used

| Model | Input / 1M tokens | Output / 1M tokens |
|-------|------------------|-------------------|
| GPT-4o-mini | $0.15 | $0.60 |
| Gemini 2.0 Flash | $0.075 | $0.30 |
| Claude 3 Haiku | $0.25 | $1.25 |

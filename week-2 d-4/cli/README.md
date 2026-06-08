# Anthropic Prompt Caching — Implementation Guide

Prompt caching lets you **mark parts of your prompt as reusable**. The API caches these on the server side for ~5 minutes. Subsequent requests that use the same cached content get **~90% cheaper reads** for those tokens.

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Request 1      │     │  Anthropic API   │     │  Response 1    │
│  ┌───────────┐  │     │                  │     │  Cost: $X      │
│  │ System    │──┼────▶│  Cache write     │◀────│  (cache write) │
│  │ (cached)  │  │     │  (expensive)     │     │                │
│  ├───────────┤  │     │                  │     │                │
│  │ Context   │──┼────▶│  Store in cache  │     │                │
│  │ (cached)  │  │     │                  │     │                │
│  └───────────┘  │     └──────────────────┘     └────────────────┘
│  New question   │
└─────────────────┘
        │  5 minutes later...
        ▼
┌─────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Request 2      │     │  Anthropic API   │     │  Response 2    │
│  ┌───────────┐  │     │                  │     │  Cost: ~$X/10  │
│  │ System    │──┼────▶│  Cache HIT!      │◀────│  (cache read)  │
│  │ (cached)  │  │     │  90% cheaper     │     │                │
│  ├───────────┤  │     │                  │     │                │
│  │ Context   │──┼────▶│  Read from cache │     │                │
│  │ (cached)  │  │     │                  │     │                │
│  └───────────┘  │     └──────────────────┘     └────────────────┘
│  New question   │
└─────────────────┘
```

## Cost Savings

| Operation | Cost per 1M tokens (Claude Sonnet 4) |
|-----------|-------------------------------------|
| **Standard input** | $3.00 |
| **Cache write** (first request) | $3.75 (25% premium) |
| **Cache read** (subsequent requests) | $0.30 (**90% cheaper**) |

**Net savings breakdown for 10 requests with identical system prompt + context:**

| Scenario | Total cost | Avg cost/request | Savings |
|----------|-----------|-----------------|---------|
| **No caching** | $30.00 | $3.00 | — |
| **With caching** | $6.45 | $0.65 | **78.5%** |

*Assumes: 1K token system prompt, 9K token context, 500 token output per request*

## Implementation

### HTTP API (curl)

```bash
curl -X POST https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: prompt-caching-2024-07-31" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "system": [
      {
        "type": "text",
        "text": "You are a code review assistant...",
        "cache_control": { "type": "ephemeral" }
      }
    ],
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "LARGE CODE CONTENT HERE...",
            "cache_control": { "type": "ephemeral" }
          }
        ]
      }
    ]
  }'
```

### Node.js (with fetch)

```javascript
const res = await fetch("https://api.anthropic.com/v1/messages", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "x-api-key": process.env.ANTHROPIC_API_KEY,
    "anthropic-version": "2023-06-01",
    "anthropic-beta": "prompt-caching-2024-07-31",
  },
  body: JSON.stringify({
    model: "claude-sonnet-4-20250514",
    max_tokens: 1024,
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
            text: codeContext,
            cache_control: { type: "ephemeral" },
          },
        ],
      },
    ],
  }),
});
```

### Python

```python
import json, os
from urllib import request

body = json.dumps({
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "system": [
        {
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }
    ],
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": code_context,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        }
    ],
}).encode()

req = request.Request(
    "https://api.anthropic.com/v1/messages",
    data=body,
    headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"],
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "prompt-caching-2024-07-31",
    },
)
resp = request.urlopen(req)
```

## Measuring Cache Savings

Look for these in the API response:

**Usage fields:**
```json
{
  "usage": {
    "input_tokens": 15000,
    "output_tokens": 500,
    "cache_creation_input_tokens": 12000,  // tokens written to cache
    "cache_read_input_tokens": 0            // tokens read from cache (0 on first request)
  }
}
```

**Response header:**
```
anthropic-cache-hit: system,content.0
```

On the second request, `cache_read_input_tokens` should be ~12000 and input cost drops from $0.045 to ~$0.009.

## When to Use Prompt Caching

| Use Case | Cache Benefit | Example |
|----------|--------------|---------|
| **System prompts** | High — same system prompt every time | Code review assistant, translator |
| **Codebase context** | High — same files explained repeatedly | Codebase explainer tool |
| **Few-shot examples** | Medium — examples used across requests | Classification with examples |
| **Large documents** | High — reference docs in every query | Legal document analysis |
| **Conversation history** | Low — changes every turn | Chatbots (not worth caching) |

## Limitations

| Limitation | Detail |
|-----------|--------|
| **Cache TTL** | ~5 minutes of inactivity |
| **Minimum cacheable size** | 1,024 tokens (smaller prompts aren't cached) |
| **Beta header required** | `anthropic-beta: prompt-caching-2024-07-31` |
| **Provider support** | Anthropic Claude only (no OpenAI/Gemini equivalent yet) |
| **Cache write premium** | 25% more expensive than standard input |

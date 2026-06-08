#!/bin/bash
# ──────────────────────────────────────────────────────────
# First curl call to Anthropic's messages.create API
# ──────────────────────────────────────────────────────────
# Usage:  export ANTHROPIC_API_KEY="sk-ant-..."
#         ./curl-call.sh
# ──────────────────────────────────────────────────────────

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "❌ ANTHROPIC_API_KEY is not set"
  echo "   export ANTHROPIC_API_KEY=sk-ant-..."
  exit 1
fi

echo "🚀 Calling Anthropic API..."
echo ""

curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 150,
    "messages": [
      {"role": "user", "content": "Say hello back to me and tell me one fun fact about ancient Rome."}
    ]
  }' | jq .

echo ""
echo "✅ Done"

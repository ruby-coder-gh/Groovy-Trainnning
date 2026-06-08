#!/bin/bash
# ──────────────────────────────────────────────────────────
# First Ollama API call — local LLM, zero cost
# ──────────────────────────────────────────────────────────
# Usage:  ./curl-call.sh
# ──────────────────────────────────────────────────────────

OLLAMA_URL="http://localhost:11434/api/chat"
MODEL="qwen3:8b"

echo "🚀 Calling Ollama API (${MODEL})..."
echo ""

curl -s --max-time 60 "${OLLAMA_URL}" \
  -H "content-type: application/json" \
  -d "{
    \"model\": \"${MODEL}\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"Say hello back to me and tell me one fun fact about ancient Rome.\"}
    ],
    \"stream\": false
  }" | jq .

echo ""
echo "✅ Done"

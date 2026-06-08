# Day 6 — Ollama API · First Call

> **Date:** Monday — Week 2 starts. Hitting local LLMs. No API key needed.

---

## 🔁 Week 1 Retro — What Worked / What Was Hard

Before diving into Week 2, we did a quick retro with the cohort.

### What Worked ✅

| Thing | Why |
|-------|-----|
| **Prompt engineering bootcamp** (Day 3) | The single highest-leverage skill. Every day since, my prompts have been way tighter. |
| **Building real things fast** | TODO app, CRUD app — having something working in 30 mins is a huge confidence boost. |
| **Context attaching in Continue.dev** | `@file`, `@folder`, `@codebase` — this alone made me 2x faster. |
| **The cohort Slack** | Seeing what others built pushed me to do better. |

### What Was Hard 😤

| Thing | Why |
|-------|-----|
| **Environment setup chaos** | Port conflicts (RIP port 5000), Node version mismatches, API keys everywhere. Day 1 was a mess. |
| **AI error handling** | The AI writes beautiful happy paths but forgets edge cases. Every. Single. Time. |
| **Knowing when NOT to use AI** | Spent 20 mins prompting for a simple regex that would've taken 2 mins to write myself. |
| **Over-relying on one model** | Claude is great at creative, ChatGPT at structured — switching between them is awkward. |

### One Thing I'm Changing This Week 🔧

> *Test the AI's output more aggressively. No more blind copy-paste. Every AI-generated block gets a quick sanity check before I commit.*

---

## 📖 Ollama API — Key Takeaways

Spent time reading the [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md).

### Why Ollama?
- **100% free** — no API keys, no credit cards, no rate limits
- **Runs locally** — everything stays on your machine
- **Multiple models** — `qwen3:8b`, `llama3`, `deepseek`, etc.
- **OpenAI-compatible** — can swap clients easily

### Auth
- None. Runs on `localhost:11434`. No headers needed.

### Models Available
| Model | Size | Notes |
|-------|------|-------|
| `qwen3:8b` | 8.2B Q4 | Good balance of speed + quality |
| `nemotron-3-ultra:cloud` | Cloud | Faster, hosted via Ollama |
| `deepseek-v3.2:cloud` | Cloud | Heavier, more capable |

We're using **qwen3:8b** as default. Fast enough, smart enough.

### Key Endpoint

```
POST http://localhost:11434/api/chat
```

### Request Body
```json
{
  "model": "qwen3:8b",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false
}
```

### Response
```json
{
  "model": "qwen3:8b",
  "message": {
    "role": "assistant",
    "content": "Hello! How can I help you today?"
  },
  "total_duration": 123456789,
  "prompt_eval_count": 10,
  "eval_count": 22
}
```

---

## 🐚 First Curl Call

```bash
curl -s http://localhost:11434/api/chat \
  -d '{
    "model": "qwen3:8b",
    "messages": [{"role": "user", "content": "Say hello back to me."}],
    "stream": false
  }' | jq .
```

📂 Full script: [`curl-call.sh`](./curl-call.sh)

### Actual Output
```json
{
  "model": "qwen3:8b",
  "message": {
    "role": "assistant",
    "content": "Hello! 😊\nA fun fact about ancient Rome: The Romans built the Cloaca Maxima, one of the world's oldest sewer systems, around 600 BCE..."
  },
  "total_duration": 17526933709,
  "prompt_eval_count": 25,
  "eval_count": 438
}
```

**First Ollama call = success.** No API key, no signup, just JSON back from a local LLM. Wild.

---

## 📦 Node.js — Multi-Turn CLI Chatbot

📂 Code: [`node-chatbot/`](./node-chatbot/)

### What it does
- CLI chatbot that maintains conversation history
- Calls Ollama API directly with built-in `fetch` (no npm deps needed)
- Stores messages array locally and sends with each turn
- Handles `exit` to quit, `/clear` to reset
- ~50 lines of actual logic

### Run it
```bash
cd node-chatbot
node index.js
```

### Code snippet
```js
const messages = [];
const rl = readline.createInterface({ input, output });

async function chat() {
  rl.question('You: ', async (input) => {
    if (input === 'exit') return rl.close();
    messages.push({ role: 'user', content: input });
    const res = await fetch('http://localhost:11434/api/chat', {
      method: 'POST',
      body: JSON.stringify({ model: 'qwen3:8b', messages, stream: false }),
    });
    const data = await res.json();
    console.log('Ollama:', data.message.content);
    messages.push({ role: 'assistant', content: data.message.content });
    chat();
  });
}
```

---

## 🐍 Python — Multi-Turn CLI Chatbot

📂 Code: [`python-chatbot/`](./python-chatbot/)

### What it does
- Same as Node version but in Python
- Uses `requests` library
- History maintained as list of dicts
- ~50 lines, same logic

### Run it
```bash
cd python-chatbot
pip install requests
python chatbot.py
```

---

## 💬 Slack Post — Week 1 Retro + Day 6

> *"Week 1 retro done ✅ — biggest win was prompt engineering (Day 3 completely changed how I talk to AI). Biggest struggle: port conflicts and knowing when NOT to use AI. Day 6 we hit the Ollama API instead — free, local, no API key needed. Node + Python chatbots are up on GitHub. Week 2 let's gooo 🔥"*

---

## Deliverable Checklist ✅

- [x] Week 1 retro — what worked / what was hard
- [x] Read Ollama API docs — models · endpoint · format
- [x] First curl call to Ollama chat endpoint
- [x] Node.js multi-turn CLI chatbot
- [x] Python multi-turn CLI chatbot
- [x] All pushed to GitHub

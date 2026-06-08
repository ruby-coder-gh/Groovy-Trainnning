# Day 6 — Anthropic API · First Call

> **Date:** Monday — Week 2 starts. We're hitting real APIs now.

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

## 📖 Anthropic API Docs — Key Takeaways

Spent time reading through the [Anthropic API docs](https://docs.anthropic.com/en/docs).

### Auth
- API key sent via `x-api-key` header
- Keys start with `sk-ant-`
- Free trial gives **$5 in credits** (no card needed for trial)
- Rate limits vary by tier — free tier is **5 requests per minute** (ish)

### Models
| Model | Best For | Context Window |
|-------|----------|---------------|
| `claude-sonnet-4-20250514` | Balanced — speed + quality | 200K tokens |
| `claude-haiku-3-5-20241022` | Fast, cheap, simple tasks | 200K tokens |

We're using **Sonnet** for most stuff. Haiku when we need speed.

### Key Endpoint

```
POST https://api.anthropic.com/v1/messages
```

### Required Headers
```
x-api-key: <your-key>
anthropic-version: 2023-06-01
content-type: application/json
```

### Request Body
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1024,
  "messages": [
    {"role": "user", "content": "Hello!"}
  ]
}
```

### Response
```json
{
  "content": [{"text": "Hi! How can I help you?", "type": "text"}],
  "model": "claude-sonnet-4-20250514",
  "role": "assistant",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 8
  }
}
```

---

## 🐚 First Curl Call

```bash
curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "Say 'Hello from curl!' back to me."}]
  }' | jq .
```

📂 Full script: [`curl-call.sh`](./curl-call.sh)

### Output
```json
{
  "id": "msg_01ABC123...",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Hello from curl! 👋 I'm Claude, and I'm happy to hear from you. How can I help you today?"
    }
  ],
  "model": "claude-sonnet-4-20250514",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 18,
    "output_tokens": 22
  }
}
```

**First API call = success.** Seeing JSON come back from a real LLM API is a nerdy kind of thrilling.

---

## 📦 Node.js SDK — Multi-Turn CLI Chatbot

📂 Code: [`node-chatbot/`](./node-chatbot/)

### What it does
- CLI chatbot that maintains conversation history
- Uses Anthropic Node.js SDK
- Stores messages array locally and sends with each turn
- Handles `exit` to quit
- ~50 lines of actual logic

### Run it
```bash
cd node-chatbot
npm install
ANTHROPIC_API_KEY=sk-ant-... node index.js
```

### Code snippet
```js
const messages = [];
const rl = readline.createInterface({ input, output });

async function chat() {
  rl.question('You: ', async (input) => {
    if (input === 'exit') return rl.close();
    messages.push({ role: 'user', content: input });
    const response = await anthropic.messages.create({ model, max_tokens: 512, messages });
    const reply = response.content[0].text;
    console.log('Claude:', reply);
    messages.push({ role: 'assistant', content: reply });
    chat();
  });
}
```

---

## 🐍 Python SDK — Multi-Turn CLI Chatbot

📂 Code: [`python-chatbot/`](./python-chatbot/)

### What it does
- Same as Node version but in Python
- Uses `anthropic` Python SDK
- History maintained as list of dicts
- ~50 lines, same logic

### Run it
```bash
cd python-chatbot
pip install anthropic
ANTHROPIC_API_KEY=sk-ant-... python chatbot.py
```

---

## 💬 Slack Post — Week 1 Retro + Day 6

> *"Week 1 retro done ✅ — biggest win was prompt engineering (Day 3 completely changed how I talk to AI). Biggest struggle: port conflicts and knowing when NOT to use AI. Also made my first raw curl call to Anthropic's API today and it FELT like magic. Node + Python chatbots are up on GitHub. Week 2 let's gooo 🔥"*

---

## Deliverable Checklist ✅

- [x] Week 1 retro — what worked / what was hard
- [x] Read Anthropic API docs — auth · models · rate limits
- [x] First curl call to `messages.create`
- [x] Node.js SDK multi-turn chatbot
- [x] Python SDK multi-turn chatbot
- [x] All pushed to GitHub

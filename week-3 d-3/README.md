# Day 13 — Tool Use · Function Calling · Agents

**Moving from "LLM that talks" → "LLM that actually does stuff."**

This is where the magic happens. Instead of just generating text, our AI agent can now search the web, crunch numbers, check the weather, look up stock prices, query databases, read files, and even send Slack messages. It's not just chat — it's an agent that acts.

---

## 🎯 The Mission

Build a tool-using agent that can:

1. **Search the web** — DuckDuckGo (free, no key needed)
2. **Do calculations** — add, subtract, multiply, divide
3. **Send notifications** — Slack webhook (or console fallback)
4. **Plus stretch tools** — weather, stocks, database, file reader

The LLM decides *which* tool to use. You just ask naturally.

---

## 🧠 How It Works

### Old school (dumb LLM):

```
User: "What's 45 * 12?"
LLM: "I don't have a calculator... but I think it's 540 maybe?"
```

### Agent flow (this project):

```
User: "What's 45 * 12?"

LLM: decides → {"tool": "calculator", "a": 45, "b": 12, "operation": "multiply"}
Tool executes: 540
LLM sees result: "45 × 12 = 540"

You get: ✅ Correct answer, every time.
```

The loop keeps going until the LLM is satisfied:

```
User Query → LLM picks tool → Run tool → LLM sees result → (repeat if needed) → Final Answer
```

Up to 5 turns max (so it doesn't loop forever and drain your wallet).

---

## 🛠️ The Tools

### Core Trio (Day 13 required)

| Tool | What it does | Powered by |
|------|-------------|------------|
| **Calculator** | Add, subtract, multiply, divide | Local Python |
| **Web Search** | Search the live internet | DuckDuckGo (free ∞) |
| **Slack** | Send messages to a channel | Webhook (or console) |

### Stretch Goals (`--stretch` flag)

| Tool | What it does | Powered by |
|------|-------------|------------|
| **Weather** | Current + 3-day forecast for any city | wttr.in (free ∞) |
| **Stock Price** | Price, change, day range, market cap | yfinance (free) |
| **Database** | Run SQL queries on sample data | SQLite |
| **File Reader** | Read text files safely | Local FS (sandboxed) |

---

## 🏛️ Architecture

```
week-3 d-3/
├── agent.py              # 🚪 CLI entry — just run this
├── agent_loop.py         # 🔄 Cohere agent loop
├── openai_agent.py       # 🔄 OpenAI agent loop
├── registry.py           # 📋 Tool directory (name → function)
├── schemas.py            # 📐 JSON schemas for LLM
├── tools/
│   ├── calculator.py     # ➕ add/subtract/multiply/divide
│   ├── web_search.py     # 🔍 DuckDuckGo search
│   ├── slack.py          # 📢 Slack webhook
│   ├── weather.py        # 🌤️ wttr.in (stretch)
│   ├── stock.py          # 📈 yfinance (stretch)
│   ├── database.py       # 🗄️ SQLite (stretch)
│   └── file_reader.py    # 📄 Safe file reading (stretch)
├── .env                  # 🔑 API keys (gitignored)
├── requirements.txt      # 📦 Python deps
└── README.md             # 📖 You are here
```

---

## 🚀 How to Run

### 1. Install stuff

```bash
pip install -r requirements.txt
pip install yfinance     # for stock tool (optional)
```

### 2. Set your API keys in `.env`

```bash
COHERE_API_KEY="your-cohere-key"     # required for Cohere backend
OPENAI_API_KEY="your-openai-key"     # required for OpenAI backend
SLACK_WEBHOOK_URL="https://..."      # optional (falls back to console)
```

### 3. Run it

```bash
# Interactive mode
python agent.py

# With all tools (including stretch)
python agent.py --stretch

# Single query
python agent.py -q "What's the weather in Tokyo?"

# Use OpenAI instead of Cohere
python agent.py --openai

# Shorthand everything
python agent.py -o -s -q "NVDA stock price"
```

---

## 🎮 CLI Commands

| Command | What it does |
|---------|-------------|
| `python agent.py` | Interactive mode, Cohere, core tools |
| `python agent.py -s` | + weather, stocks, DB, file tools |
| `python agent.py -o` | Use OpenAI backend |
| `python agent.py -o -s` | OpenAI + all 7 tools |
| `python agent.py -q "query"` | Single query, get answer, exit |
| `python agent.py --model gpt-5` | Override model name |

Inside interactive mode:
- Type anything → agent picks the tool
- `tools` → see what's available
- `exit` or `q` → leave

---

## 🎬 Live Demos

### Calculator
```
You:  What is 245 * 88?

Agent thinks:  "I should use the calculator tool"
               → calculator(245, 88, "multiply")

Agent:  245 × 88 = 21,560 ✅
```

### Web Search
```
You:  Search latest NVIDIA news

Agent thinks:  "Let me search the web for this"
               → search_web("latest NVIDIA news 2026")

Agent:  Here's what I found...
        1. NVIDIA and LG building AI factory...
        2. Jensen Huang calls selloff a buying opportunity...
```

### Weather
```
You:  What's the weather in Tokyo?

Agent thinks:  "Weather check incoming"
               → get_weather("Tokyo")

Agent:  Tokyo is 22°C, partly cloudy. Humidity 78%.
        Wind is 18 km/h. UV index is low. 🌤️
```

### Multi-tool (the flex)
```
You:  Search for AI news and send the top story to Slack

Turn 1 → search_web("top AI news today") → gets results
Turn 2 → send_slack("Top story: ...")    → sends it

Agent:  Done! Sent the top AI story to Slack. 📢
```

---

## 📐 JSON Schema — How the LLM Knows What Tools Exist

Every tool has a schema. This is the contract between the LLM and the tool system.

```python
# Example: Calculator Schema
{
    "name": "calculator",
    "description": "Perform basic arithmetic",
    "parameters": {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"},
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"]
            }
        },
        "required": ["a", "b", "operation"]
    }
}
```

The LLM reads this and knows:
- "Oh, there's a `calculator` tool"
- "It takes two numbers and an operation"
- "Operation must be one of these 4 values"

**Quality of descriptions matters.** If you write a bad description, the LLM picks the wrong tool. Garbage in, garbage out.

---

## 🔁 Tool Registry

`registry.py` is the central directory. Every tool lives here:

```python
REGISTRY = {
    "calculator": {
        "function": calculate,
        "schema": calculate.SCHEMA,
    },
    "search_web": {
        "function": search_web,
        "schema": search_web.SCHEMA,
    },
    # ... add your own tool in 2 lines
}
```

Adding a new tool = import it + add one dict entry. That's it.

---

## 🧪 Backend Options

### Cohere (default)
- Model: `command-r-08-2024`
- Schema format: Native tool calling
- File: `agent_loop.py`

### OpenAI
- Model: `gpt-4o`
- Schema format: Function calling (`{type: "function", function: {...}}`)
- File: `openai_agent.py`

Both share the **same tools, same registry, same schemas**. Only the API call changes.

---

## 🌟 Stretch Tools Deep Dive

### Weather (`get_weather`)
- Uses wttr.in — free forever, zero API keys
- Returns: temp, feels-like, humidity, wind, UV, description
- Optional 3-day forecast

### Stock Price (`get_stock_price`)
- Uses yfinance — free, no key
- Returns: price, change ±%, day range, volume, market cap, P/E
- Falls back to finnhub.io if yfinance missing

### Database (`query_database`)
- Runs any SQL against local SQLite
- Comes with sample data: 8 products, 6 orders, 4 users
- Set it up: `python -c "from tools.database import setup_sample_database; setup_sample_database()"`

### File Reader (`read_file`)
- Reads text files from your machine
- **Safety first:** blocks `/etc`, `~/.ssh`, `~/.aws`, etc.
- Only text extensions allowed (no binaries)
- Max 500 lines / 1 MB

---

## 💡 Stuff I Learned

- **Function calling = superpower.** Giving an LLM structured tool access turns it from a chat bot into an agent that can actually change things.
- **Schema descriptions are everything.** The LLM reads your tool descriptions to decide what to use. Write them well or watch it fail hilariously.
- **Registry pattern is clean AF.** Add a tool in 2 lines. Remove one in 1 line. No spaghetti.
- **Multiple backends, one codebase.** Cohere and OpenAI have different API formats, but the tools don't care. Abstraction for the win.
- **Safety isn't optional.** File reader needs path blocking, extension whitelisting, and size limits. Give an agent unrestricted file access and you're asking for trouble.
- **Multi-turn loops are powerful but need limits.** 5 max turns keeps your API bills in check while still handling complex workflows (search → calculate → notify).
- **Error tolerance matters.** Every tool wraps exceptions and returns strings. The LLM sees "API rate limited" and can say "Sorry, try again later" instead of crashing.

---

## 📦 Dependencies

```
cohere>=5.0.0            # LLM backend (Cohere)
ddgs                     # DuckDuckGo search (free)
requests>=2.31.0         # HTTP calls
python-dotenv>=1.0.0     # .env loading
yfinance                 # Stock prices (stretch, optional)
openai                   # OpenAI backend (optional)
```

---

*Built in ~4 hours. One week deeper into the agentic rabbit hole. 🕳️🐇*

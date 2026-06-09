# 🎯 Groovy AI Agent

**A lightweight, pure-Python agent that summarises meetings, processes daily standups, and keeps your team in sync — without burning your laptop or your wallet.**

```
                         🤖  AGENT LOOP
                                     
    📥 INPUT ──→  🤔 THINK  ──→  🛠️  ACT  ──→  👀 OBSERVE  ──→  ✅ RESULT
                      │               │                │
                      │         ┌─────┴─────┐          │
                      │         │  Gemini   │          │
                      │         │  (Free)   │          │
                      │         └─────┬─────┘          │
                      │               │                │
                      ▼               ▼                ▼
                   💾 SQLite       📤 Slack        📂 GitHub
```

---

## 🧠 What Is This?

This is **your final evolution project** — an AI agent built from scratch using nothing but:

| Ingredient | Why | Cost |
|-----------|-----|------|
| **Python** (pure — no LangGraph, no CrewAI) | You trace every line of the agent loop | ₹0 |
| **Google Gemini Free API** | Cloud LLM, zero RAM on your Mac | ₹0 |
| **SQLite** (stdlib) | Portable, persistent memory | ₹0 |
| **Slack Webhook** (stdlib) | Team notifications | ₹0 |
| **GitHub API** (stdlib) | Code context when needed | ₹0 |

**RAM usage:** ~100 MB  
**Your MacBook temp:** cool as a cucumber  
**Demo impressiveness:** chef's kiss  

---

## 🌍 Real-World Scenario

> It's Tuesday morning at Groovy. You're the only engineer who notices that the team is drowning in meetings and nobody remembers who owns what.

**Before the agent:**
- Alice attends 3 back-to-back meetings, takes notes in a private doc
- Bob forgets the action item he volunteered for yesterday
- Charlie posts his standup in Slack at 10 AM but nobody reads it
- Diana spends 20 minutes copying action items into Jira
- The sprint retro has zero data — everyone goes by memory

**After the agent:**
1. Alice drops the meeting transcript into the agent
2. Within seconds, Gemini extracts summary + action items + owners
3. Everything is saved in SQLite — queryable forever
4. The team gets a Slack notification with the summary
5. At standup, everyone submits updates → agent generates team status
6. Managers can query "What were the blockers last week?" in seconds

**The agent doesn't replace anyone. It just makes sure nothing falls through the cracks.**

---

## 🏗️ Architecture

### The Agent Loop (pure Python, ~150 lines)

```
┌────────────────────────────────────────────────────────┐
│                    AGENT LOOP                          │
│                                                        │
│   RECEIVE  ──→  THINK  ──→  ACT  ──→  OBSERVE  ──→   │
│   (input)      (plan)    (call     (parse      (output)│
│                           tool)     result)            │
│                               │                        │
│                               ▼                        │
│                         ┌─────────┐                    │
│                         │  Tools   │                    │
│                         │ ┌──────┐ │                    │
│                         │ │Gemini│ │  ← LLM reasoning  │
│                         │ ├──────┤ │                    │
│                         │ │SQLite│ │  ← memory         │
│                         │ ├──────┤ │                    │
│                         │ │Slack │ │  ← notify         │
│                         │ ├──────┤ │                    │
│                         │ │GitHub│ │  ← code context   │
│                         │ └──────┘ │                    │
│                         └─────────┘                    │
└────────────────────────────────────────────────────────┘
```

### Why No LangGraph / CrewAI / MCP?

> *"I wanted to understand the agent loop first and build a lightweight, production-ready solution using pure Python, Gemini API, SQLite, and Slack integration. The architecture can later be migrated to LangGraph or other frameworks if needed."*

That's the answer. It's honest, it shows depth, and it's exactly what senior engineers want to hear.

---

## 🚀 Quick Start

### 1. Get your free API key

Go to [Google AI Studio](https://aistudio.google.com/apikey) and click "Create API key". It's free. No credit card needed.

### 2. Setup

```bash
# Navigate to the project
cd "week-6 d-5/ai-agent"

# Install dependencies (just one!)
pip install -r requirements.txt

# Set your API key
export GEMINI_API_KEY="your-key-here"

# Optional: set up Slack (still works without it)
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
```

### 3. Run the Meeting Summary Agent

```bash
# Demo mode (built-in sample transcript)
python run_meeting_agent.py --demo

# From a file
python run_meeting_agent.py --file transcript.txt --title "Sprint Retro"

# Interactive (paste your own transcript)
python run_meeting_agent.py

# See every decision the agent makes
python run_meeting_agent.py --demo --verbose
```

### 4. Run the Daily Standup Agent

```bash
# Demo mode
python run_standup_agent.py --demo

# Interactive mode (enter updates one by one)
python run_standup_agent.py

# From a JSON file
python run_standup_agent.py --file examples/standup_data.json

# See the full agent trace
python run_standup_agent.py --demo --verbose
```

### 5. Run Everything at Once

```bash
python examples/demo_all_in_one.py
```

This runs both agents back-to-back with sample data and shows the full trace.

---

## 📁 Project Structure

```
ai-agent/
├── README.md                 ← You're reading it!
├── requirements.txt          ← Just `google-genai` — that's it
├── .env.example              ← Copy to .env for your keys
├── run_meeting_agent.py      ← Meeting summary entry point
├── run_standup_agent.py      ← Daily standup entry point
├── src/
│   ├── agent.py              ← 🧠 THE AGENT LOOP (core brain)
│   ├── tools/
│   │   ├── base.py           ← Abstract Tool class
│   │   ├── gemini_tool.py    ← Gemini API wrapper
│   │   ├── sqlite_tool.py    ← Database operations
│   │   ├── slack_tool.py     ← Slack webhook
│   │   └── github_tool.py    ← GitHub API reader
│   ├── models/
│   │   └── schema.py         ← SQLite schema + data access
│   └── prompts/
│       └── templates.py      ← Prompt templates for Gemini
├── data/
│   └── agent_memory.db       ← SQLite DB (auto-created)
├── examples/
│   └── demo_all_in_one.py    ← Full demo script
└── tests/
    └── test_agent.py         ← 20+ tests (mocked APIs)
```

---

## 🛠️ Tools Explained

### 1. Gemini Tool (`gemini_tool.py`)
Wraps the Google Gemini Free API. The free tier (`gemini-2.0-flash`) is fast, smart, and costs nothing. The tool supports both free-text and structured (JSON mode) responses.

```python
tool = GeminiTool(api_key="...")
result = tool(system="You are a summariser", prompt="Summarise this...")
print(result.data["text"])
```

### 2. SQLite Tool (`sqlite_tool.py`)
Every meeting and standup gets saved to a local `agent_memory.db` file. No server, no config, no cloud bill. You can query it with any SQLite browser.

```python
tool = SQLiteTool(db_path="data/agent_memory.db")
tool.execute(action="save_meeting", title="Sprint", summary="...")
tool.execute(action="list_recent_meetings", limit=5)
```

### 3. Slack Tool (`slack_tool.py`)
Posts rich, formatted messages to any Slack channel via incoming webhook. Works with any Slack workspace — free tier included.

```python
tool = SlackTool(webhook_url="https://hooks.slack.com/...")
tool.send_summary("Summary text...", "Meeting Title")
tool.send_standup("Team status...")
```

### 4. GitHub Tool (`github_tool.py`)
Reads files from public (or private) repos. Useful when the agent needs code context.

```python
tool = GitHubTool()
result = tool(action="get_file", repo="owner/repo", path="README.md")
```

---

## 🧪 Running Tests

```bash
# Install test dependency
pip install pytest

# Run all tests (mocked — no API keys needed)
python -m pytest tests/ -v

# Run tests with coverage (optional)
python -m pytest tests/ --cov=src --cov-report=term-missing
```

Tests cover:
- SQLite read/write operations
- Slack webhook posting (mocked)
- GitHub API responses (mocked)
- Prompt template formatting
- Agent trace recording
- Meeting summary parsing
- Action item extraction
- Standup pipeline
- Error handling

---

## 📊 What You Can Demo

| Scenario | Command | Wow Factor |
|----------|---------|------------|
| Meeting transcript → summary + actions | `python run_meeting_agent.py --demo` | ⭐⭐⭐⭐⭐ |
| Team standup → AI-generated status | `python run_standup_agent.py --demo` | ⭐⭐⭐⭐ |
| Full pipeline + Slack notification | Add `SLACK_WEBHOOK_URL` | ⭐⭐⭐⭐⭐ |
| Agent trace (think → act → observe) | `--verbose` flag | ⭐⭐⭐⭐ |
| Query past meetings from SQLite | `sqlite3 data/agent_memory.db` | ⭐⭐⭐ |
| Everything at once | `python examples/demo_all_in_one.py` | ⭐⭐⭐⭐⭐ |

---

## 💡 Why This Works on Your MacBook

| Component | RAM | Why It's Fine |
|-----------|-----|---------------|
| Python process | ~30-50 MB | Lightweight interpreter |
| Your code | ~1 MB | Pure Python, no heavy libs |
| Gemini API | 0 MB | Runs on Google's servers |
| SQLite | ~2 MB | Embedded, no server |
| Total | **~55 MB** | You have ~8 GB free |

No GPU needed. No 7B models. No Ollama. No fan noise.



## 🎓 What You Learned

By building this project, you demonstrated:

1. **Agent Architecture** — You built a proper think-act-observe loop from scratch
2. **Tool Abstraction** — Every capability is wrapped in a consistent `Tool` interface
3. **LLM Integration** — You used Google's free Gemini API effectively
4. **Persistence** — SQLite for structured memory
5. **Notifications** — Slack webhook integration
6. **Error Handling** — Every tool call is wrapped, traced, and debuggable
7. **Testing** — 20+ tests with mocked external services
8. **Prompt Engineering** — Crafted system prompts for structured output
9. **Production Mindset** — Logging, tracing, configuration, CLI ergonomics
10. **Communication** — This README

---

## 🏁 Final Word

> *"The best architecture is the one you can trace end-to-end."*

This agent isn't a black box. Every `think`, every `act`, every `observe` is logged, traceable, and debuggable. That's not a limitation — that's a superpower.

**You built this. Own it. Demo it. Ship it.** 🚀

---

*Built with ☕, Python, and Google's free Gemini API — June 2026*

# Day 14 — Multi-Step Agents: LangChain vs LlamaIndex vs Pure SDK

**What separates an AI Engineer from someone who only knows prompts.**

Today we build the SAME agent 3 different ways — LangChain, LlamaIndex, and raw OpenAI SDK. Then we compare them head-to-head and add memory systems so the agent actually remembers stuff.

---

## 🎯 The Mission

Build a multi-step agent that can:

1. **Think** — break down complex queries into steps
2. **Use tools** — calculator, web search, time, string ops
3. **Loop** — keep going until the answer is complete
4. **Remember** — short-term (conversation) + long-term (facts)

And do it all **3 different ways** so you understand what's framework magic vs what's actually happening under the hood.

---

## 🧠 What is a Multi-Step Agent?

### Simple chatbot (dumb):
```
You: "Find NVIDIA stock and calculate cost of 10 shares"
LLM: "I don't have live data... but NVIDIA is a company that makes GPUs."
```

### Multi-step agent (smart):
```
You: "Find NVIDIA stock and calculate cost of 10 shares"

Step 1 → LLM: "I need the stock price"
         🔧 search_web("NVDA stock price") → $208.64

Step 2 → LLM: "Now I calculate 208.64 × 10"
         🔧 calculator(208.64, 10, "multiply") → 2086.40

Step 3 → LLM: "10 shares of NVDA cost $2,086.40"
```

The LLM doesn't just answer — it **reasons**, **decides what to do**, **executes**, and **loops** until done.

---

## 🏛️ Architecture

```
week-3 d-4/
├── agent.py                    # 🚪 Main CLI — pick your framework
├── compare.py                  # 📊 Runs same query on all 3 + compares
├── 1-langchain-agent/
│   └── agent.py                # 🔵 LangChain agent
├── 2-llamaindex-agent/
│   ├── agent.py                # 🟢 LlamaIndex RAG agent
│   └── data/sample.txt         # Sample doc about NVIDIA/AI
├── 3-pure-sdk-agent/
│   └── agent.py                # ⚪ Pure OpenAI SDK (no framework)
├── 4-memory/
│   ├── short_term.py           # 🧠 Sliding window conversation buffer
│   └── long_term.py            # 🗄️ SQLite persistent memory
├── .env                        # 🔑 API keys
└── requirements.txt            # 📦 Python deps
```

---

## 🔵 Part 1: LangChain Agent

LangChain is the most popular agent framework. It has a huge ecosystem but a LOT of abstractions.

```python
from langchain.agents import initialize_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

agent = initialize_agent(
    tools=[calculator, search, time],
    llm=ChatOpenAI(model="gpt-4o"),
    agent="zero-shot-react-description",
    verbose=True
)

agent.invoke("What is 25 * 18?")
```

**What happens inside:**
```
Thought: I need to multiply 25 and 18
Action: Calculator("25 * 18")
Observation: 450
Thought: I now know the answer
Final: 25 multiplied by 18 equals 450.
```

**Pros:** Huge ecosystem, fast prototyping
**Cons:** Abstractions leak, debugging is painful, versions change weekly

Run it:
```bash
python agent.py langchain -q "What is 25 * 18?"
```

---

## 🟢 Part 2: LlamaIndex Agent

LlamaIndex shines at RAG (Retrieval-Augmented Generation). It's built for document pipelines.

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.llms.openai import OpenAI

docs = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(docs)
engine = index.as_query_engine()

response = engine.query("What does NVIDIA do?")
```

**What happens inside:**
```
Document → Chunking → Embeddings → Vector Search → Context → LLM → Answer
```

Then we add a calculator tool on top so it can also do math.

**Pros:** Best RAG pipeline, clean API
**Cons:** Smaller ecosystem, agent support is weaker

Run it:
```bash
python agent.py llamaindex -q "What does NVIDIA do?"
```

---

## ⚪ Part 3: Pure SDK Agent (The Most Important One)

**No framework. Just OpenAI SDK. This is the real skill.**

```python
def agent_loop(user_query, max_turns=5):
    messages = [{"role": "user", "content": user_query}]
    
    for turn in range(max_turns):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOL_SCHEMAS,
        )
        
        msg = response.choices[0].message
        
        if not msg.tool_calls:
            return msg.content  # Final answer!
        
        messages.append(msg)
        
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = TOOL_FUNCTIONS[tc.function.name](**args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result),
            })
    
    return "Max turns reached"
```

**This is EXACTLY what LangChain and LlamaIndex do internally.** Every framework eventually runs this loop. Understanding it = understanding all of them.

**Pros:** Full control, fastest, easiest to debug, production-ready
**Cons:** You write more code, you need to understand the loop

Run it:
```bash
python agent.py pure-sdk -q "What is 25 * 18?"
```

---

## 🔄 The Universal Agent Loop

Every framework runs the same core loop:

```
while True:
    response = llm(messages, tools)     # Ask LLM
    if response.has_tool_call():         # Does LLM want a tool?
        result = execute_tool(response)  # Run it
        messages.append(result)          # Give result back
    else:
        return response                  # Done!
```

That's it. Everything else — chains, graphs, pipelines — is just decoration around this loop.

---

## 🧠 Part 5: Short-Term Memory

Keeps the current conversation in a sliding window.

```python
from memory.short_term import ShortTermMemory

mem = ShortTermMemory(window_size=10)
mem.add_user("What is AI?")
mem.add_assistant("AI is artificial intelligence.")
mem.add_user("Tell me more.")

context = mem.get_context()  # Last 10 messages
```

- Stores messages with roles (user, assistant, tool, system)
- Sliding window keeps context bounded (no infinite growth)
- System message always stays at position 0

---

## 🗄️ Part 6: Long-Term Memory

Stores facts across sessions using SQLite.

```python
from memory.long_term import LongTermMemory

mem = LongTermMemory()
mem.remember("name", "Nikunj")
mem.remember("goal", "Become an AI Engineer")

# Later...
name = mem.recall("name")          # "Nikunj"
facts = mem.search("AI")           # Search by keyword
context = mem.format_context()     # Ready for LLM prompt injection
```

**Flow:**
```
User Query → Memory Search → Relevant Facts → Prompt → LLM → Answer
```

This is how assistants become personalized. ChatGPT does this. Claude does this. Now you do too.

---

## 📊 Comparison: LangChain vs LlamaIndex vs Pure SDK

| Feature | LangChain | LlamaIndex | Pure SDK |
|---------|-----------|------------|----------|
| **Learning Curve** | Medium | Medium | High (but worth it) |
| **Flexibility** | Medium | Medium | 🔥 Very High |
| **RAG Quality** | Good | 🔥 Excellent | Manual |
| **Debugging** | Hard (abstractions) | Medium | 🔥 Easy (no magic) |
| **Speed** | Medium | Medium | 🔥 Fast |
| **Production** | Okay | Okay | 🔥 Best |
| **Ecosystem** | 🔥 Huge | Medium | N/A (raw SDK) |
| **Code You Write** | Little | Little | More |
| **What You Learn** | How to use LangChain | How to use LlamaIndex | 🔥 How agents actually work |

### When to use what:

| Situation | Pick |
|-----------|------|
| **Learning how agents work** | Pure SDK |
| **Fast prototyping** | LangChain |
| **RAG / document Q&A** | LlamaIndex |
| **Production startup** | Pure SDK + custom code |
| **When you need every integration** | LangChain |

### The Hard Truth:

> Most companies start with LangChain, fight it for 6 months, then rewrite in Pure SDK.

Understanding the Pure SDK loop means you can use ANY framework effectively because you know what's happening under the hood.

---

## 🚀 How to Run

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Set API key in `.env`

```
OPENAI_API_KEY="sk-..."
```

### 3. Run any agent

```bash
# LangChain agent
python agent.py langchain -q "What is 25 * 18?"

# LlamaIndex RAG agent
python agent.py llamaindex -q "What does NVIDIA do?"

# Pure SDK agent (no framework)
python agent.py pure-sdk -q "Reverse the word 'artificial'"

# Interactive mode (just omit -q)
python agent.py langchain

# Memory demo
python agent.py memory

# Run comparison (all 3 on same queries)
python agent.py compare
```

---

## 🎬 Live Demos

### LangChain: Multi-step math
```
You:  What is 15 + 37 and then multiply by 2?

Thought: I need to calculate 15 + 37 first
Action: Calculator("15 + 37") → 52
Thought: Now multiply 52 by 2
Action: Calculator("52 * 2") → 104
Final: (15 + 37) × 2 = 104 ✅
```

### LlamaIndex: RAG query
```
You:  What is NVIDIA's market share in AI chips?

Retrieved: "NVIDIA continues to dominate the AI chip market
            with over 80% market share"
Answer: NVIDIA holds over 80% of the AI chip market. ✅
```

### Pure SDK: Multi-tool
```
You:  What's the current time, and reverse the word "agent"?

Turn 1 → current_time() → "2026-06-09 12:30:00"
Turn 2 → reverse_string("agent") → "tnega"
Final: The time is 2026-06-09 12:30:00, and "agent" reversed is "tnega". ✅
```

---

## 💡 Stuff I Learned

- **All frameworks are the same loop.** LangChain, LlamaIndex, CrewAI, AutoGen — they all run `while True: llm(messages, tools)`. Once you see it, you can't unsee it.
- **Pure SDK teaches you the most.** Building the loop yourself removes all the magic. When something breaks in LangChain, you'll actually understand why.
- **LangChain abstractions leak.** The `verbose=True` output shows crazy prompts that LangChain auto-generates. Cool for prototyping, terrifying for debugging.
- **LlamaIndex is best at ONE thing.** RAG. If you're building a document Q&A system, it's the best choice. If you're building general agents, it's not.
- **Memory is what makes agents personal.** Short-term = conversation context. Long-term = user profile. Both are simple to implement (list + SQLite) but transform the user experience.
- **Multi-step is where agents earn their keep.** One-shot queries are easy. Multi-step (search → calculate → notify) is where the agent actually proves it's thinking.
- **Comparison reports are worth it.** Running the same query through all 3 side-by-side makes the tradeoffs obvious immediately.

---

## 📦 Dependencies

```
langchain>=0.3.0           # 🔵 LangChain framework
langchain-openai>=0.2.0    # OpenAI integration for LangChain
langchain-community>=0.3.0 # Community tools (DuckDuckGo)
llama-index>=0.12.0        # 🟢 LlamaIndex framework
openai>=1.55.0             # ⚪ OpenAI SDK (Pure SDK agent)
python-dotenv>=1.0.0       # .env loading
```

---

*Built in ~5 hours. Three frameworks, one loop, zero magic. 🎩✨*

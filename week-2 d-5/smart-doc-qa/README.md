# 📘 Smart Doc Q&A — Ask Your Notes, Get Answers

> **Upload a PDF. Ask anything. Get answers with page citations — 100% local & free.**

Hey there! 👋 Welcome to **Smart Doc Q&A** — a little web app that lets you upload a PDF and chat with it. Think of it like "ChatGPT, but for *your* documents." No more skimming through 50 pages for that one stat. Just upload, ask, and boom. 💥

Built for **Mini-Project 2** of our training cohort. Uses **Ollama** running locally with the **qwen3:8b** model — so it's **completely free** and your docs never leave your machine. 🏠

---

## ✨ What It Does

| Feature | Why It's Cool |
|---|---|
| 📄 **Upload any PDF** | Drag-drop or click to upload. Handles big docs (up to 50 MB). |
| 💬 **Ask questions** | Type a question, get a natural-language answer. |
| 📎 **Page-number citations** | Every answer tells you *exactly* which page(s) the info came from. |
| 💰 **Cost telemetry** | See tokens used in real-time right in the header (always $0!). |
| 🏠 **100% local** | Ollama runs on your machine — no cloud, no API keys, no privacy worries. |

---

## 🏗 Architecture

```
┌─────────────┐     POST /api/upload     ┌──────────────┐    HTTP /api/chat    ┌───────────┐
│  React SPA  │ ──────────────────────► │  Node/Express │ ──────────────────► │  Ollama   │
│  (Port 3000)│ ◄────────────────────── │  (Port 3001)  │ ◄────────────────── │ qwen3:8b  │
│             │     JSON responses       │               │     tokens+answer   └───────────┘
└─────────────┘                          └──────────────┘
       │                                        │
       │  Cost telemetry                        │  PDF parsing (pdfjs-dist v3)
       │  every 5s                              │  Per-page text extraction
       ▼                                        ▼
  ╔══════════════════════╗          ╔══════════════════════╗
  ║  Token usage badge   ║          ║  Pages[1..N] in mem  ║
  ║  in app header       ║          ║  (no DB, no Redis)   ║
  ╚══════════════════════╝          ╚══════════════════════╝
```

### Stack

- **Frontend:** React 18, plain CSS (custom dark theme, no frameworks)
- **Backend:** Node.js + Express
- **AI:** Ollama (qwen3:8b) — 100% local inference
- **PDF parsing:** pdfjs-dist v3 (per-page text extraction)
- **File uploads:** Multer (multipart/form-data)

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** v18 or later
- **Ollama** installed locally → [ollama.com/download](https://ollama.com/download)
- **qwen3:8b model** pulled:

```bash
ollama pull qwen3:8b
```

### 1. Clone & Install

```bash
git clone https://github.com/ruby-coder-gh/Groovy-Trainnning.git
cd Groovy-Trainnning/10/smart-doc-qa

# Install server dependencies
cd server && npm install

# Install client dependencies
cd ../client && npm install
```

### 2. Make Sure Ollama Is Running

```bash
ollama serve          # Start Ollama if not already running
ollama list           # Should show qwen3:8b
```

### 3. Fire It Up

Open **two terminals**:

```bash
# Terminal 1 — API Server (no API key needed!)
cd server
npm run dev
# → http://localhost:3001

# Terminal 2 — React Client
cd client
npm start
# → http://localhost:3000
```

### 4. Upload & Ask!

1. Open `http://localhost:3000` in your browser
2. Drag a PDF into the upload zone (or click to browse)
3. Click **Upload & Parse**
4. Type your question in the chat box
5. Read the answer with **page-number citations** in the sidebar

---

## 📡 API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a PDF (multipart/form-data, field: `pdf`) |
| `POST` | `/api/ask` | Ask a question (`{ "question": "..." }`) |
| `GET` | `/api/cost` | Get accumulated token usage & cost |
| `GET` | `/api/document` | Get current document info |
| `GET` | `/api/health` | Health check 🩺 |

### Example: Ask a Question

```bash
curl -X POST http://localhost:3001/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the key findings on page 3?"}'
```

**Response:**
```json
{
  "answer": "Based on the document, the key findings on [Page 3] include...",
  "citations": [
    { "page": 3, "excerpt": "The key findings show that..." }
  ],
  "cost": {
    "model": "qwen3:8b",
    "inputTokens": 442,
    "outputTokens": 309,
    "sessionCost": 0,
    "accumulatedCost": 0
  }
}
```

---

## 💰 Cost Telemetry

The header shows a live-updating cost badge (refreshes every 5 seconds):

```
┌─────────────────────────────────────────────────────┐
│  Model     │  Tokens In  │  Tokens Out  │ Cost      │
│  qwen3:8b  │  1,309      │  904         │ $0.0000   │
└─────────────────────────────────────────────────────┘
```

**Because Ollama runs locally, every answer costs exactly $0.00.** 💸

The token counter is still useful though — it shows you how much context your PDF uses and how verbose the model is being.

---

## 📁 Project Structure

```
smart-doc-qa/
├── client/                    # React frontend
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js             # Main app with state management
│   │   ├── App.css            # All styles (dark theme)
│   │   ├── index.js           # React entry point
│   │   └── components/
│   │       ├── FileUpload.js      # Drag-drop PDF upload
│   │       ├── ChatInterface.js   # Chat messages + input
│   │       ├── CostTelemetry.js   # Cost badge component
│   │       └── SourceCitations.js # Citation sidebar cards
│   └── package.json
├── server/                    # Node.js API
│   ├── index.js               # Express server entry
│   ├── routes/
│   │   └── qa.js              # Upload + ask + cost routes
│   ├── services/
│   │   ├── pdfParser.js       # PDF extraction (pdfjs-dist v3)
│   │   └── geminiService.js   # Actually Ollama! (kept name for laughs)
│   └── package.json
└── README.md                  # You are here 🌟
```

> 😅 Yes, the service file is still called `geminiService.js` — we started with Anthropic, swapped to Gemini, and ended on Ollama. The name's a fossil. Deal with it.

---

## 🧠 How Answering Works (The Smart Part)

1. **Upload phase:** PDF is parsed with **pdfjs-dist v3**, extracting text **per page** — no hacky form-feed splitting.
2. **Storage:** Pages stay in memory as `[{ pageNumber: 1, text: "..." }, ...]` — no database, no vector store.
3. **Question time:** When you ask something, the entire document text is sent to **Ollama** with page-number prefixes (`[Page 1]`, `[Page 2]`, etc.).
4. **System prompt:** The model is instructed to cite page numbers like `[Page 3]` or `[Pages 4-5]` in every answer.
5. **Citation extraction:** After Ollama responds, the app parses the answer for `[Page N]` patterns and extracts matching text snippets for the sidebar.
6. **Token tracking:** Every Ollama response includes `prompt_eval_count` and `eval_count`, which are accumulated and exposed via `/api/cost`.

---

## 🧪 Demo Plan (10 Minutes)

| Time | What |
|---|---|
| **0:00** | Open the app, show the UI, explain the stack |
| **0:30** | Upload a PDF (I'll use a sample report) |
| **1:00** | Ask 3 questions — show citations working |
| **2:00** | Show the cost telemetry (always $0!) |
| **2:30** | Peek at the code: prompt engineering & citation extraction |
| **4:00** | Talk about architecture decisions (why Ollama, no DB) |
| **5:00** | Discuss what's next (RAG, streaming, better citations) |
| **6:00** | Q&A |

---

## 🛣 Roadmap / What's Next

- [ ] **Vector database integration** (Chroma or pgvector) for scalable RAG
- [ ] **Streaming responses** with Server-Sent Events (SSE)
- [ ] **Support multiple file formats** (`.docx`, `.txt`, `.md`)
- [ ] **Better citation parsing** — extract exact quotes, not just page numbers
- [ ] **Chat history persistence** (localStorage or a simple DB)
- [ ] **Docker Compose** for one-command setup
- [ ] **Model selector** in the UI — pick between Ollama models on the fly

---

## 🤝 Cohort Retrospective Notes

**What went well:**
- Ollama is a dream for local AI — no API keys, no rate limits, no costs
- React + Express is still the GOAT for prototyping
- Page-number citations blow people's minds in demos
- Swapping AI providers 3 times (Anthropic → Gemini → Ollama) taught us a lot!

**What I'd do differently:**
- Shoulda used TypeScript from the start 🙃
- Shoulda used pdfjs-dist from day 1 instead of fighting with pdf-parse
- Cost telemetry should use WebSockets instead of polling
- Service file naming is a mess (anthropicService → geminiService → actually Ollama 😅)

**Shoutout:** To the cohort for the feedback during sprint retro — the citation sidebar was totally their idea!

---

## 📬 Questions?

Ping me on Slack or catch me at standup! Happy to pair on the RAG integration.

---

<p align="center">
  <sub>Built with ❤️, ☕, and Ollama · Mini-Project 2 · June 2026</sub>
</p>

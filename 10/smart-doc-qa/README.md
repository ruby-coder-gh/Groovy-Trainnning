# 📘 Smart Doc Q&A — Ask Your Notes, Get Answers

> **Upload a PDF. Ask anything. Get answers with page citations.**

Hey there! 👋 Welcome to **Smart Doc Q&A** — a little web app I built that lets you upload a PDF and chat with it. Think of it like "ChatGPT, but for *your* documents." No more skimming through 50 pages looking for that one stat — just upload, ask, and boom. 💥

Built for **Mini-Project 2** of our training cohort. Live demo to the squad in 10 minutes flat. Let's go!

---

## ✨ What It Does

| Feature | Why It's Cool |
|---|---|
| 📄 **Upload any PDF** | Drag-drop or click to upload. Handles big docs (up to 50 MB). |
| 💬 **Ask questions** | Type a question, get a natural-language answer. |
| 📎 **Page-number citations** | Every answer tells you *exactly* which page(s) the info came from. |
| 💰 **Cost telemetry** | See tokens used and total cost in real-time right in the header. |
| ⚡ **No vector DB (yet)** | Pure Claude magic for now — RAG coming soon! |

---

## 🏗 Architecture

```
┌─────────────┐     POST /api/upload     ┌──────────────┐     Anthropic API     ┌───────────┐
│  React SPA  │ ──────────────────────► │  Node/Express │ ──────────────────► │ Claude 3  │
│  (Port 3000)│ ◄────────────────────── │  (Port 3001)  │ ◄────────────────── │  Haiku    │
│             │     JSON responses       │               │     tokens+cost     └───────────┘
└─────────────┘                          └──────────────┘
       │                                        │
       │  Cost telemetry                        │  PDF parsing (pdf-parse)
       │  every 5s                              │  In-memory storage
       ▼                                        ▼
  ╔══════════════════════╗          ╔══════════════════════╗
  ║  Real-time cost bar  ║          ║  Pages with metadata ║
  ║  in app header       ║          ║  (no DB, no Redis)   ║
  ╚══════════════════════╝          ╚══════════════════════╝
```

### Stack

- **Frontend:** React 18, plain CSS (custom dark theme, no frameworks)
- **Backend:** Node.js + Express
- **AI:** Anthropic Claude 3 Haiku (fast + cheap)
- **PDF parsing:** `pdf-parse`
- **File uploads:** Multer (multipart/form-data)

---

## 🚀 Getting Started

### Prerequisites

- **Node.js** v18 or later
- **An Anthropic API key** — grab one at [console.anthropic.com](https://console.anthropic.com)

### 1. Clone & Install

```bash
git clone https://github.com/nikunjvaghasiya/smart-doc-qa.git
cd smart-doc-qa

# Install server dependencies
cd server && npm install

# Install client dependencies
cd ../client && npm install
```

### 2. Set Your API Key

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

> 💡 Pro tip: Add this to your `.zshrc` or `.bashrc` so you don't have to type it every time.

### 3. Fire It Up

Open **two terminals**:

```bash
# Terminal 1 — API Server
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
4. Wait for the green checkmark
5. Type your question in the chat box
6. Read the answer with **clickable page citations** in the sidebar

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
    "model": "claude-3-haiku-20240307",
    "inputTokens": 1542,
    "outputTokens": 312,
    "sessionCost": 0.0015,
    "accumulatedCost": 0.0087
  }
}
```

---

## 💰 Cost Telemetry

The header shows a live-updating cost badge (refreshes every 5 seconds):

```
┌─────────────────────────────────────────────────────┐
│  Model         │  Tokens In  │  Tokens Out  │ Cost │
│  claude-3-haiku│  12,847     │  3,201       │ $0.01│
└─────────────────────────────────────────────────────┘
```

**Pricing (Claude 3 Haiku):**
| Direction | Price per 1M tokens |
|---|---|
| Input | $0.25 |
| Output | $1.25 |

At these rates, a typical 10-page PDF with 5 questions costs **less than a penny**. 💸

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
│   │   ├── pdfParser.js       # PDF text extraction
│   │   └── anthropicService.js # Claude API + cost tracking
│   └── package.json
└── README.md                  # You are here 🌟
```

---

## 🧠 How Answering Works (The Smart Part)

1. **Upload phase:** PDF is parsed with `pdf-parse`, text is split into pages using form-feed characters.
2. **Storage:** Pages stay in memory as `[{ pageNumber: 1, text: "..." }, ...]` — no database, no vector store.
3. **Question time:** When you ask something, the entire document text is sent to Claude with page-number prefixes (`[Page 1]`, `[Page 2]`, etc.).
4. **System prompt:** Claude is instructed to cite page numbers like `[Page 3]` or `[Pages 4-5]` in every answer.
5. **Citation extraction:** After Claude responds, the app parses the answer for `[Page N]` patterns and extracts matching text snippets.
6. **Cost tracking:** Every API response includes token counts, which are accumulated server-side and exposed via `/api/cost`.

> 🔮 **Future:** Once we add a vector DB (Chroma, Pinecone, or pgvector), we'll store page embeddings and retrieve only the *relevant* pages per question — making it faster, cheaper, and scalable to 1,000+ page docs.

---

## 🧪 Demo Plan (10 Minutes)

| Time | What |
|---|---|
| **0:00** | Open the app, show the UI, explain the stack |
| **0:30** | Upload a PDF (I'll use a sample report) |
| **1:00** | Ask 3 questions — show citations working |
| **2:00** | Show the cost telemetry ticking up |
| **2:30** | Peek at the code: prompt engineering & citation extraction |
| **4:00** | Talk about architecture decisions (no DB, why Haiku) |
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
- [ ] **Deploy to Railway / Render / Fly.io**

---

## 🤝 Cohort Retrospective Notes

**What went well:**
- Anthropic API is a dream to work with — clean SDK, great docs
- React + Express is still the GOAT for prototyping
- Page-number citations blow people's minds in demos

**What I'd do differently:**
- Shoulda used TypeScript from the start 🙃
- PDF page-splitting with form-feeds is hacky — need a proper per-page parser
- Cost telemetry should use WebSockets instead of polling

**Shoutout:** To the cohort for the feedback during sprint retro — the citation sidebar was totally their idea!

---

## 📬 Questions?

Ping me on Slack or catch me at standup! Happy to pair on the RAG integration.

---

<p align="center">
  <sub>Built with ❤️, ☕, and Claude 3 Haiku · Mini-Project 2 · June 2026</sub>
</p>

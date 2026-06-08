# Day 2 — AI-IDE Deep Dive · Free Tier

> **Date:** Tuesday — today we build. No mouse. Just prompts.
> **Repo:** https://github.com/ruby-coder-gh/Groovy-Trainnning.git

---

## Morning — Live Demo 🤯

Senior dev hopped on a screenshare and showed us Continue.dev / Cline shortcuts in real time. I thought I knew what AI coding looked like. I did NOT know.

Some shortcuts I'm now addicted to:

| Shortcut | What it does |
|----------|-------------|
| `Cmd+I` | Inline chat — ask anything about the line you're on |
| `Cmd+L` | Full side-panel chat with context |
| `Cmd+Shift+L` | Quick fix suggestion |
| `@file` | Tag a specific file as context |
| `@folder` | Tag a whole folder as context |
| `@codebase` | Let the AI scan the entire repo |

The **context attaching** part was the real eye-opener. You can literally say:

> *"Hey, look at this file (@file:server.js), understand the route pattern, then look at this folder (@folder:models) and generate a new model following the same convention."*

And it just... works. Like having a junior dev who reads at 10x speed.

---

## The Challenge — Build a TODO App With Only Prompts 📱

Alright. This was the main event. **React frontend + Node backend. Zero manual coding. Only prompts.**

I called it **PROMTODO** — because the prompts *are* the code.

### The Plan

```
promtodo/
├── client/          ← React app (Vite)
├── server/          ← Node.js + Express API
└── README.md        ← Every single prompt documented
```

---

## All Prompts Used (Raw & Unfiltered) 🗂️

Here's every prompt I threw at the AI. Some hit, some missed, all taught me something.

### Prompt #1 — Project Scaffold
```
Create a project folder called "promtodo". Inside it, set up:
- /client using Vite + React (JavaScript)
- /server using Node.js + Express
- Initialize package.json for both
- No TypeScript please I'm too sleepy for types today
```

**Result:** ✅ Folders created, dependencies installed, basic scripts in place.

---

### Prompt #2 — Backend API
```
In /server, create an Express server with:
- GET /api/todos — returns all todos
- POST /api/todos — creates a new todo (accepts {title, completed})
- PUT /api/todos/:id — updates a todo
- DELETE /api/todos/:id — deletes a todo
- Use an in-memory array (no DB, we're keeping it simple)
- Add CORS so the React app can talk to it
- Listen on port 5001 (5000 was taken by macOS ControlCe — classic Apple things)
- Add a little startup message so I know it's alive
```

**Result:** ✅ Clean REST API. AI even added error handling without me asking.

---

### Prompt #3 — Backend Fix (The Fail)
```
Wait, POST /api/todos should return the created todo with an ID.
Currently it's just returning the body. Fix it.
```

**Result:** ❌ The AI added an ID but used `crypto.randomUUID()` which Node 18+ has. Mine was on Node 16. Had to ask for a fix.

**Follow-up prompt:**
```
Use Date.now() + Math.random().toString() for the ID instead.
can't use crypto.randomUUID() because Node version is old :')
```

**Result:** ✅ Worked.

---

### Prompt #4 — React App Scaffold
```
In /client, create a simple TODO app with:
- A text input + "Add" button at the top
- A list that shows all todos
- Each todo shows its title and a checkbox
- Clicking the checkbox toggles the completed state
- Each todo has a "Delete" button (red, scary looking)
- Fetch todos from http://localhost:5001/api/todos on load
- POST to create, PUT to update, DELETE to remove
- Style it with basic CSS (not ugly but not overkill)
- Use plain fetch, no axios
```

**Result:** ✅ Full CRUD frontend. Working. Magic.

---

### Prompt #5 — UI Polish
```
Make the app look less like it's from 2005.
- Center everything on the page
- Add a nice font (Google Fonts — Inter)
- Smooth hover effects on buttons
- Completed todos should have a strikethrough + fade out
- Add a counter below the list: "3 items left"
- Gradient background please (subtle, not mySpace era)
```

**Result:** ✅ Honestly? Looked better than most production apps I've seen.

---

### Prompt #6 — Loading & Error States (Prompted by Senior Review)
```
Add a loading spinner when fetching todos.
Add an error message that shows if the backend is down.
Style both of them nicely.
```

**Result:** ✅ Added a spinning animation and a sad little error box. Cute and functional.

---

### Prompt #7 — README Documentation
```
Write a README.md for the entire project that:
- Explains what PROMTODO is
- Lists all the prompts I used (in a table)
- Has a "What AI did well" section
- Has a "What AI failed at" section
- Installation instructions
- Screenshot placeholder
```

**Result:** ✅ Meta, right? I'm literally typing the output of this prompt right now.

---

## Senior Code Review 👀

Had a senior dev look at my code. Here's the honest feedback:

### 👍 What AI Did Well
> *"The component structure is actually clean. It split the TodoItem into its own component, used proper hooks, and even handled edge cases like empty states. If you told me a human wrote this, I'd believe you."*

The AI naturally followed **React best practices** — functional components, hooks, proper state management. Without me even asking.

### 👎 What AI Failed At
> *"Error handling is inconsistent. The PUT request doesn't catch network errors properly, and if the server sends a non-200 response, the UI just silently fails. Also, no input validation — you can add an empty todo title."*

100% valid. The AI wrote the happy path beautifully but got lazy on edge cases. Classic.

**What I learned:** AI is great at the 80% solution. The last 20% (error handling, edge cases, security) still needs a human brain.

---

## Pushed to GitHub 🐙

All code pushed to: **[Groovy-Trainnning](https://github.com/ruby-coder-gh/Groovy-Trainnning.git)**

```bash
git add 1/ 2/
git commit -m "Day 1 + Day 2: Setup, AI-IDE deep dive, PROMTODO app"
git push origin main
```

Repo URL shared on Slack with the caption:

> *"Built an entire TODO app without touching the keyboard (except for typing prompts). This is wild. Link in thread."*

The cohort reacted with fire emojis. One person asked *"wait how much did you actually code though"* and I said *"nothing. i just argued with an AI for 2 hours."*

---

## Final Thoughts 💭

Building with prompts only is a **wildly different** experience from traditional coding:

- **Speed:** 10x faster for the first version
- **Debugging:** 2x slower when something breaks (you have to prompt your way out)
- **Learning:** You still need to understand code to guide the AI
- **Fun factor:** Off the charts

The TODO app works. It's on GitHub. All prompts are documented.

**Day 2 done. Bring on Day 3.** 🚀

---

## Deliverable Checklist ✅

- [x] Attended live demo on Continue.dev / Cline shortcuts
- [x] Practiced context attaching (file · folder · codebase)
- [x] Built TODO app with prompts only (React + Node)
- [x] Documented every prompt in this README
- [x] Pushed to GitHub + shared repo URL on Slack
- [x] Code review with senior — noted 1 win + 1 fail

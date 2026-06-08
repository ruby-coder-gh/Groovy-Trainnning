# 📋 PROMTODO

> A full-stack TODO app built **entirely from AI prompts**.  
> React frontend + Node/Express backend. Zero manual coding.

Built as part of **Day 2 — AI-IDE Deep Dive** of the AI Bootcamp.

---

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- npm

### 1. Start the Server
```bash
cd server
npm install
npm start
```
Server runs at `http://localhost:5000`

### 2. Start the Client
```bash
cd client
npm install
npm run dev
```
Client runs at `http://localhost:3000`

---

## 🧠 All Prompts Used

Every single prompt that built this app. Raw, unfiltered, as-is.

### Prompt #1 — Project Scaffold
> Create a project folder called "promtodo". Inside it, set up:
> - /client using Vite + React (JavaScript)
> - /server using Node.js + Express
> - Initialize package.json for both
> - No TypeScript please I'm too sleepy for types today

**✅ Result:** Folders created, dependencies wired, scripts ready.

---

### Prompt #2 — Backend API
> In /server, create an Express server with:
> - GET /api/todos — returns all todos
> - POST /api/todos — creates a new todo (accepts {title, completed})
> - PUT /api/todos/:id — updates a todo
> - DELETE /api/todos/:id — deletes a todo
> - Use an in-memory array (no DB, we're keeping it simple)
> - Add CORS so the React app can talk to it
> - Listen on port 5000
> - Add a little startup message so I know it's alive

**✅ Result:** Clean REST API with proper status codes and error responses.

---

### Prompt #3 — Backend Fix (The Fail)
> Wait, POST /api/todos should return the created todo with an ID.
> Currently it's just returning the body. Fix it.

**❌ Result:** AI used `crypto.randomUUID()` — not available on Node 16.

**Follow-up:**
> Use Date.now() + Math.random().toString() for the ID instead.
> can't use crypto.randomUUID() because Node version is old :')

**✅ Result:** Fixed. 🎉

---

### Prompt #4 — React App Scaffold
> In /client, create a simple TODO app with:
> - A text input + "Add" button at the top
> - A list that shows all todos
> - Each todo shows its title and a checkbox
> - Clicking the checkbox toggles the completed state
> - Each todo has a "Delete" button (red, scary looking)
> - Fetch todos from http://localhost:5000/api/todos on load
> - POST to create, PUT to update, DELETE to remove
> - Style it with basic CSS (not ugly but not overkill)
> - Use plain fetch, no axios

**✅ Result:** Full CRUD frontend. Components split nicely.

---

### Prompt #5 — UI Polish
> Make the app look less like it's from 2005.
> - Center everything on the page
> - Add a nice font (Google Fonts — Inter)
> - Smooth hover effects on buttons
> - Completed todos should have a strikethrough + fade out
> - Add a counter below the list: "3 items left"
> - Gradient background please (subtle, not mySpace era)

**✅ Result:** Clean, modern look. Gradient is *chef's kiss*.

---

### Prompt #6 — Loading & Error States
> Add a loading spinner when fetching todos.
> Add an error message that shows if the backend is down.
> Style both of them nicely.

**✅ Result:** Spinner animation + dismissable error box.

---

### Prompt #7 — This README
> Write a README.md for the entire project that:
> - Explains what PROMTODO is
> - Lists all the prompts I used (in a table)
> - Has a "What AI did well" section
> - Has a "What AI failed at" section
> - Installation instructions
> - Screenshot placeholder

**✅ Result:** You're reading it. Meta, right?

---

## ✅ What AI Did Well

- **Component structure** — naturally split `App`, `TodoItem`, `LoadingSpinner`, `ErrorMessage` without being told
- **React hooks** — `useState` + `useEffect` usage was clean and idiomatic
- **REST conventions** — proper HTTP methods, status codes, JSON responses
- **CSS quality** — hover states, transitions, responsive layout, gradient — all solid
- **Error handling basics** — caught fetch errors, showed user feedback

## ❌ What AI Failed At

- **Node version assumption** — used `crypto.randomUUID()` which isn't in Node 16. Had to prompt-fix it
- **Input validation** — initially didn't check for empty todo titles on the backend
- **Inconsistent error handling** — the PUT endpoint didn't catch network errors as thoroughly as GET/POST
- **Delete response** — initially returned the deleted object instead of a 204 (minor, but不规范)

## 💭 Verdict

> AI is incredible at the **first 80%** — structure, patterns, conventions.  
> The **last 20%** (edge cases, error states, compatibility) still needs a human eyeball.

But still — built a full-stack app without typing a single line of logic by hand.  
That's not nothing. 🚀

const express = require("express");
const cors = require("cors");

const app = express();
const PORT = 5001;

app.use(cors());
app.use(express.json());

// ─── In-memory database ──────────────────────────────────────────
let todos = [];
let nextId = 1;

// ─── Routes ──────────────────────────────────────────────────────

// GET /api/todos — return all todos
app.get("/api/todos", (req, res) => {
  res.json(todos);
});

// POST /api/todos — create a new todo
app.post("/api/todos", (req, res) => {
  const { title } = req.body;

  if (!title || !title.trim()) {
    return res.status(400).json({ error: "Title is required" });
  }

  const todo = {
    id: Date.now(),
    title: title.trim(),
    completed: false,
  };

  todos.push(todo);
  res.status(201).json(todo);
});

// PUT /api/todos/:id — update a todo (toggle completed or edit title)
app.put("/api/todos/:id", (req, res) => {
  const id = parseInt(req.params.id);
  const todo = todos.find((t) => t.id === id);

  if (!todo) {
    return res.status(404).json({ error: "Todo not found" });
  }

  const { title, completed } = req.body;

  if (title !== undefined) {
    if (!title.trim()) {
      return res.status(400).json({ error: "Title cannot be empty" });
    }
    todo.title = title.trim();
  }

  if (completed !== undefined) {
    todo.completed = completed;
  }

  res.json(todo);
});

// DELETE /api/todos/:id — delete a todo
app.delete("/api/todos/:id", (req, res) => {
  const id = parseInt(req.params.id);
  const index = todos.findIndex((t) => t.id === id);

  if (index === -1) {
    return res.status(404).json({ error: "Todo not found" });
  }

  todos.splice(index, 1);
  res.status(204).send();
});

// ─── Start ───────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`🚀 PROMTODO server running at http://localhost:${PORT}`);
});

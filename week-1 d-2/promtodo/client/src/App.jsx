import { useState, useEffect } from "react";
import TodoItem from "./components/TodoItem";
import LoadingSpinner from "./components/LoadingSpinner";
import ErrorMessage from "./components/ErrorMessage";

const API = "http://localhost:5001/api/todos";

export default function App() {
  const [todos, setTodos] = useState([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ─── Fetch todos on mount ────────────────────────────────────────
  useEffect(() => {
    fetchTodos();
  }, []);

  const fetchTodos = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(API);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setTodos(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ─── Add todo ────────────────────────────────────────────────────
  const addTodo = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;

    try {
      setError(null);
      const res = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title.trim() }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || "Failed to add todo");
      }

      const newTodo = await res.json();
      setTodos((prev) => [...prev, newTodo]);
      setTitle("");
    } catch (err) {
      setError(err.message);
    }
  };

  // ─── Toggle todo ────────────────────────────────────────────────
  const toggleTodo = async (id, completed) => {
    try {
      setError(null);
      const res = await fetch(`${API}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ completed: !completed }),
      });

      if (!res.ok) throw new Error("Failed to update todo");

      const updated = await res.json();
      setTodos((prev) => prev.map((t) => (t.id === id ? updated : t)));
    } catch (err) {
      setError(err.message);
    }
  };

  // ─── Delete todo ────────────────────────────────────────────────
  const deleteTodo = async (id) => {
    try {
      setError(null);
      const res = await fetch(`${API}/${id}`, { method: "DELETE" });

      if (!res.ok) throw new Error("Failed to delete todo");

      setTodos((prev) => prev.filter((t) => t.id !== id));
    } catch (err) {
      setError(err.message);
    }
  };

  const itemsLeft = todos.filter((t) => !t.completed).length;

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>📋 promtodo</h1>
          <p className="subtitle">built by prompts, powered by AI</p>
        </header>

        <form className="add-form" onSubmit={addTodo}>
          <input
            className="add-input"
            type="text"
            placeholder="What needs to be done?"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <button className="add-btn" type="submit">
            Add
          </button>
        </form>

        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}

        {loading ? (
          <LoadingSpinner />
        ) : todos.length === 0 ? (
          <p className="empty-state">No todos yet. Add one above! ✨</p>
        ) : (
          <>
            <ul className="todo-list">
              {todos.map((todo) => (
                <TodoItem
                  key={todo.id}
                  todo={todo}
                  onToggle={toggleTodo}
                  onDelete={deleteTodo}
                />
              ))}
            </ul>

            <p className="items-left">
              <strong>{itemsLeft}</strong> item{itemsLeft !== 1 ? "s" : ""} left
            </p>
          </>
        )}
      </div>
    </div>
  );
}

export default function TodoItem({ todo, onToggle, onDelete }) {
  return (
    <li className={`todo-item ${todo.completed ? "completed" : ""}`}>
      <label className="todo-label">
        <input
          type="checkbox"
          checked={todo.completed}
          onChange={() => onToggle(todo.id, todo.completed)}
          className="todo-checkbox"
        />
        <span className="todo-title">{todo.title}</span>
      </label>
      <button
        className="delete-btn"
        onClick={() => onDelete(todo.id)}
        title="Delete todo"
      >
        ✕
      </button>
    </li>
  );
}

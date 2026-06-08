export default function ErrorMessage({ message, onDismiss }) {
  return (
    <div className="error-box">
      <span>⚠️ {message}</span>
      <button className="error-dismiss" onClick={onDismiss}>
        ✕
      </button>
    </div>
  );
}

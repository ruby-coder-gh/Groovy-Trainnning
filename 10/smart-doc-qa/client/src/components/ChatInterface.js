import React, { useState } from 'react';

function ChatInterface({ messages, isLoading, onSend, disabled, chatEndRef }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading || disabled) return;

    onSend(trimmed);
    setInput('');
  };

  const renderMessageText = (text) => {
    // Highlight [Page N] references
    const parts = text.split(/(\[Page(?:s)?\s*[\d\s–\-—,]+\])/gi);
    return parts.map((part, i) => {
      if (/\[Page(?:s)?\s*[\d\s–\-—,]+\]/i.test(part)) {
        return (
          <span key={i} className="page-ref">
            {part}
          </span>
        );
      }
      return part;
    });
  };

  return (
    <>
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-state">
            <div>
              <div className="empty-icon">📘</div>
              <h3>Ask anything about your document</h3>
              <p>
                Upload a PDF using the sidebar, then ask questions.
                The AI will answer with page-number citations.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.role === 'assistant' ? renderMessageText(msg.text) : msg.text}
          </div>
        ))}

        {isLoading && (
          <div className="message assistant" style={{ opacity: 0.7 }}>
            <span className="typing-indicator">Thinking</span>
            <span className="dots">
              <span>.</span>
              <span>.</span>
              <span>.</span>
            </span>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <div className="chat-input-area">
        <form className="chat-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              disabled
                ? 'Upload a PDF to start asking questions...'
                : 'Ask a question about your document...'
            }
            disabled={disabled || isLoading}
            autoFocus={!disabled}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading || disabled}
            className={isLoading ? 'loading' : ''}
          >
            {isLoading ? '⏳' : '🚀 Send'}
          </button>
        </form>
      </div>
    </>
  );
}

export default ChatInterface;

import React, { useState, useCallback, useEffect, useRef } from 'react';
import FileUpload from './components/FileUpload';
import ChatInterface from './components/ChatInterface';
import CostTelemetry from './components/CostTelemetry';
import SourceCitations from './components/SourceCitations';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

function App() {
  const [documentInfo, setDocumentInfo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [costData, setCostData] = useState(null);
  const [error, setError] = useState(null);
  const [currentCitations, setCurrentCitations] = useState([]);
  const chatEndRef = useRef(null);

  // Fetch cost telemetry periodically
  useEffect(() => {
    const fetchCost = async () => {
      try {
        const res = await fetch(`${API_BASE}/cost`);
        if (res.ok) {
          const data = await res.json();
          setCostData(data);
        }
      } catch {
        // silent — server might not be running yet
      }
    };

    fetchCost();
    const interval = setInterval(fetchCost, 5000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleUploadComplete = useCallback((doc) => {
    setDocumentInfo(doc);
    setMessages([
      {
        role: 'system',
        text: `📄 Uploaded **${doc.fileName}** (${doc.totalPages} page${doc.totalPages === 1 ? '' : 's'}). Ask me anything about it!`,
      },
    ]);
    setCurrentCitations([]);
    setError(null);
  }, []);

  const handleAskQuestion = useCallback(async (question) => {
    if (!documentInfo) return;

    // Add user message
    const userMsg = { role: 'user', text: question };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);
    setCurrentCitations([]);

    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.error || 'Failed to get answer');
      }

      const data = await res.json();

      const assistantMsg = { role: 'assistant', text: data.answer };
      setMessages((prev) => [...prev, assistantMsg]);
      setCurrentCitations(data.citations || []);
      setCostData((prev) => ({
        ...prev,
        ...data.cost,
      }));
    } catch (err) {
      setError(err.message);
      setMessages((prev) => [
        ...prev,
        { role: 'system', text: `❌ ${err.message}` },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [documentInfo]);

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>
            <span className="logo-icon">📘</span> Smart Doc Q&A
          </h1>
          <p className="subtitle">
            Upload a PDF and ask questions — get answers with page citations
          </p>
        </div>
        {costData && <CostTelemetry costData={costData} />}
      </header>

      <main className="app-main">
        <aside className="sidebar">
          <FileUpload
            apiBase={API_BASE}
            onUploadComplete={handleUploadComplete}
            onError={setError}
          />

          {currentCitations.length > 0 && (
            <SourceCitations citations={currentCitations} />
          )}

          {documentInfo && (
            <div className="doc-info-card">
              <h3>📄 Current Document</h3>
              <p className="doc-name">{documentInfo.fileName}</p>
              <p className="doc-meta">
                {documentInfo.totalPages} page{documentInfo.totalPages === 1 ? '' : 's'} ·{' '}
                {new Date(documentInfo.uploadedAt).toLocaleTimeString()}
              </p>
            </div>
          )}
        </aside>

        <section className="chat-area">
          <ChatInterface
            messages={messages}
            isLoading={isLoading}
            onSend={handleAskQuestion}
            disabled={!documentInfo}
            chatEndRef={chatEndRef}
          />

          {error && !isLoading && (
            <div className="error-toast">
              <span>⚠️</span> {error}
              <button onClick={() => setError(null)}>&times;</button>
            </div>
          )}
        </section>
      </main>

      <footer className="app-footer">
        <p>
          Powered by <strong>Claude 3 Haiku</strong> via Anthropic ·
          No vector database (yet) ·
          <a
            href="https://github.com/nikunjvaghasiya/smart-doc-qa"
            target="_blank"
            rel="noopener noreferrer"
          >
            GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

export default App;

const express = require('express');
const cors = require('cors');
const path = require('path');
const qaRoutes = require('./routes/qa');

const app = express();
const PORT = process.env.PORT || 3001;

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------
app.use(cors());
app.use(express.json());

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------
app.use('/api', qaRoutes);

// Health check
app.get('/api/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ---------------------------------------------------------------------------
// Serve React build in production
// ---------------------------------------------------------------------------
if (process.env.NODE_ENV === 'production') {
  const clientBuild = path.join(__dirname, '..', 'client', 'build');
  app.use(express.static(clientBuild));
  app.get('*', (_req, res) => {
    res.sendFile(path.join(clientBuild, 'index.html'));
  });
}

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------
app.use((err, _req, res, _next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  console.log(`
  ╔══════════════════════════════════════════════╗
  ║   Smart Doc Q&A — API Server                 ║
  ║   Listening on http://localhost:${PORT}        ║
  ║   Endpoints:                                 ║
  ║     POST /api/upload   — Upload PDF          ║
  ║     POST /api/ask      — Ask a question      ║
  ║     GET  /api/cost     — Cost telemetry      ║
  ║     GET  /api/health   — Health check        ║
  ╚══════════════════════════════════════════════╝
  `);
});

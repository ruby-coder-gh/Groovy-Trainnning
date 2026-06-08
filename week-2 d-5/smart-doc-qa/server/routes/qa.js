const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { parsePdf } = require('../services/pdfParser');
const { askQuestion, getCostTelemetry, resetCost } = require('../services/geminiService');

// ---------------------------------------------------------------------------
// Multer setup — store uploads in /tmp
// ---------------------------------------------------------------------------
const uploadDir = path.join(__dirname, '..', 'uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadDir),
  filename: (_req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
    cb(null, uniqueSuffix + '-' + file.originalname);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 50 * 1024 * 1024 }, // 50 MB
  fileFilter: (_req, file, cb) => {
    if (file.mimetype !== 'application/pdf') {
      return cb(new Error('Only PDF files are allowed'));
    }
    cb(null, true);
  },
});

// In-memory document store (no vector DB yet)
let currentDocument = null;

// ---------------------------------------------------------------------------
// POST /api/upload  — upload a PDF and parse it
// ---------------------------------------------------------------------------
router.post('/upload', (req, res) => {
  upload.single('pdf')(req, res, async (err) => {
    if (err) {
      return res.status(400).json({
        error: err.message || 'Upload failed',
      });
    }

    if (!req.file) {
      return res.status(400).json({ error: 'No PDF file provided' });
    }

    try {
      const filePath = req.file.path;
      const doc = await parsePdf(filePath);

      currentDocument = {
        fileName: req.file.originalname,
        pages: doc.pages,
        totalPages: doc.totalPages,
        uploadedAt: new Date().toISOString(),
      };

      // Clean up the uploaded file
      fs.unlink(filePath, () => {});

      // Reset cost for new document session
      resetCost();

      res.json({
        message: 'Document uploaded successfully',
        document: {
          fileName: currentDocument.fileName,
          totalPages: currentDocument.totalPages,
          uploadedAt: currentDocument.uploadedAt,
        },
      });
    } catch (parseErr) {
      console.error('PDF parse error:', parseErr);
      res.status(500).json({ error: 'Failed to parse PDF: ' + parseErr.message });
    }
  });
});

// ---------------------------------------------------------------------------
// POST /api/ask  — ask a question about the uploaded document
// ---------------------------------------------------------------------------
router.post('/ask', async (req, res) => {
  const { question } = req.body;

  if (!question || typeof question !== 'string' || question.trim().length === 0) {
    return res.status(400).json({ error: 'Question is required' });
  }

  if (!currentDocument) {
    return res.status(400).json({
      error: 'No document uploaded yet. Please upload a PDF first.',
    });
  }

  try {
    const result = await askQuestion(question.trim(), currentDocument.pages);
    res.json({
      answer: result.answer,
      citations: result.citations,
      cost: result.cost,
    });
  } catch (err) {
    console.error('Ask error:', err);
    res.status(500).json({ error: err.message || 'Failed to get answer' });
  }
});

// ---------------------------------------------------------------------------
// GET /api/cost  — get cost telemetry
// ---------------------------------------------------------------------------
router.get('/cost', (_req, res) => {
  res.json(getCostTelemetry());
});

// ---------------------------------------------------------------------------
// GET /api/document  — get current document info
// ---------------------------------------------------------------------------
router.get('/document', (_req, res) => {
  if (!currentDocument) {
    return res.json({ document: null });
  }
  res.json({
    document: {
      fileName: currentDocument.fileName,
      totalPages: currentDocument.totalPages,
      uploadedAt: currentDocument.uploadedAt,
    },
  });
});

module.exports = router;

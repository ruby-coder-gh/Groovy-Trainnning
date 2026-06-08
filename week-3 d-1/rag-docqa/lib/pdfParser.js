// ─────────────────────────────────────────────────────────────────────
// PDF Parser — extracts text from PDF files (wraps pdfjs-dist v3)
//
// Uses pdfjs-dist v3.x which is stable in Node.js
// ─────────────────────────────────────────────────────────────────────

"use strict";

const fs = require("fs");
const pdfjsLib = require("pdfjs-dist");

/**
 * Extract text content from a PDF file, returning per-page text.
 */
async function parsePdf(filePath) {
  const buffer = fs.readFileSync(filePath);
  const data = new Uint8Array(buffer);

  const loadingTask = pdfjsLib.getDocument({ data });
  const pdfDoc = await loadingTask.promise;

  const totalPages = pdfDoc.numPages;
  const pages = [];

  for (let i = 1; i <= totalPages; i++) {
    try {
      const page = await pdfDoc.getPage(i);
      const content = await page.getTextContent();
      const text = content.items.map((item) => item.str).join(" ").trim();

      pages.push({
        pageNumber: i,
        text: text || `[Page ${i} appears to be empty or image-based]`,
      });
    } catch (pageErr) {
      pages.push({
        pageNumber: i,
        text: `[Error reading page ${i}: ${pageErr.message}]`,
      });
    }
  }

  const fullText = pages.map((p) => `[Page ${p.pageNumber}]\n${p.text}`).join("\n\n");

  return { pages, totalPages, fullText };
}

module.exports = { parsePdf };

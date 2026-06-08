// ─────────────────────────────────────────────────────────────────────
// Chunker — splits documents into chunks for embedding + retrieval
//
// Strategies:
//   1. Recursive character split (default)
//   2. Sentence-aware split (respects sentence boundaries)
//   3. Page-aware split (one chunk per page)
// ─────────────────────────────────────────────────────────────────────

"use strict";

const DEFAULT_CHUNK_SIZE = 500;    // target tokens (≈2000 chars)
const DEFAULT_OVERLAP  = 50;       // tokens of overlap between chunks
const CHARS_PER_TOKEN  = 4;        // approximate

/**
 * Split text into chunks using recursive character splitting.
 * Tries to break at natural boundaries: \n\n → \n → . → space
 */
function chunkText(text, options = {}) {
  const maxChars  = (options.chunkSize  || DEFAULT_CHUNK_SIZE) * CHARS_PER_TOKEN;
  const overlapChars = (options.overlap || DEFAULT_OVERLAP)   * CHARS_PER_TOKEN;

  if (!text || text.length <= maxChars) {
    return [{ text, index: 0 }];
  }

  const chunks = [];
  const separators = ["\n\n", "\n", ". ", " ", ""];

  let start = 0;
  let chunkIndex = 0;

  while (start < text.length) {
    let end = Math.min(start + maxChars, text.length);

    // Try to find a good break point near the end boundary
    if (end < text.length) {
      let bestBreak = -1;
      for (const sep of separators) {
        const idx = text.lastIndexOf(sep, end);
        if (idx > start && idx > bestBreak) {
          bestBreak = idx + sep.length;
          if (sep === ". ") break; // prefer sentence breaks
        }
      }
      if (bestBreak > start) {
        end = bestBreak;
      }
    }

    const chunkText = text.slice(start, end).trim();
    if (chunkText) {
      chunks.push({ text: chunkText, index: chunkIndex++ });
    }

    // Move start — overlap means we go back by overlapChars
    start = Math.max(start, end - overlapChars);
  }

  return chunks;
}

/**
 * Chunk an array of pages (from PDF parser).
 * Each page is { pageNumber, text }.
 * Returns chunks with page numbers for citation tracking.
 */
function chunkPages(pages, options = {}) {
  const allChunks = [];

  for (const page of pages) {
    const pageChunks = chunkText(page.text, options);
    for (const c of pageChunks) {
      allChunks.push({
        text: c.text,
        index: allChunks.length,
        pageNumber: page.pageNumber,
        source: `Page ${page.pageNumber}`,
      });
    }
  }

  return allChunks;
}

/**
 * Estimate token count for a string (used for budget tracking).
 */
function estimateTokens(text) {
  return Math.ceil((text || "").length / CHARS_PER_TOKEN);
}

module.exports = { chunkText, chunkPages, estimateTokens };

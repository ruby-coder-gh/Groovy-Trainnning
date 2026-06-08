const fs = require('fs');
const pdfParse = require('pdf-parse');

/**
 * Extract text content from a PDF buffer,
 * returning an array of { pageNumber, text } chunks.
 */
async function parsePdf(filePath) {
  const buffer = fs.readFileSync(filePath);

  const data = await pdfParse(buffer);

  // pdf-parse gives us data.text (full), data.numpages,
  // and data.textpage (if available) — but not per-page arrays directly.
  // We do a simple heuristic split on form-feed chars for page boundaries.
  const pageTexts = splitIntoPages(data.text, data.numpages);

  return {
    pages: pageTexts.map((text, i) => ({
      pageNumber: i + 1,
      text: text.trim(),
    })),
    totalPages: data.numpages,
    fullText: data.text,
  };
}

/**
 * Split full text into pages using form-feed characters.
 * pdf-parse often inserts \f (form-feed) between pages.
 */
function splitIntoPages(fullText, expectedNumPages) {
  const pages = fullText.split('\f').filter((p) => p.trim().length > 0);

  // If splitting didn't work (no form-feeds), return whole text as one page
  if (pages.length === 0) {
    return [fullText];
  }

  // Sometimes pdf-parse includes an empty last page
  if (pages.length > expectedNumPages) {
    return pages.slice(0, expectedNumPages);
  }

  return pages;
}

module.exports = { parsePdf };

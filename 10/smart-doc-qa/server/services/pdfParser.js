const fs = require('fs');
const pdfjsLib = require('pdfjs-dist');

// pdfjs-dist v3 can work without a worker in Node.js
// by using the `getDocument` with `disableWorker: true`
// or by setting a dummy worker. We'll use the built-in worker.

/**
 * Extract text content from a PDF file,
 * returning per-page text as an array of { pageNumber, text }.
 */
async function parsePdf(filePath) {
  const buffer = fs.readFileSync(filePath);
  const data = new Uint8Array(buffer);

  // Load the PDF document
  const loadingTask = pdfjsLib.getDocument({ data });
  const pdfDoc = await loadingTask.promise;

  const totalPages = pdfDoc.numPages;
  const pages = [];

  for (let i = 1; i <= totalPages; i++) {
    const page = await pdfDoc.getPage(i);
    const content = await page.getTextContent();
    const text = content.items
      .map((item) => item.str)
      .join(' ');

    pages.push({
      pageNumber: i,
      text: text.trim(),
    });
  }

  // Build full text as well
  const fullText = pages.map((p) => `[Page ${p.pageNumber}]\n${p.text}`).join('\n\n');

  return {
    pages,
    totalPages,
    fullText,
  };
}

module.exports = { parsePdf };

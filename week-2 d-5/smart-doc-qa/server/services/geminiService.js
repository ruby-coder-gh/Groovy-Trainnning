// ---------------------------------------------------------------------------
// Ollama Service — runs models locally (FREE, no API key needed!)
// Uses qwen3:8b — fast, capable, runs on your machine
// ---------------------------------------------------------------------------

const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://localhost:11434';
const MODEL = process.env.OLLAMA_MODEL || 'qwen3:8b';

// Accumulated cost is always $0 (local models are free!)
let accumulatedCost = 0;
let totalInputTokens = 0;
let totalOutputTokens = 0;

/**
 * Ask a question about a document using Ollama.
 * @param {string} question - The user's question.
 * @param {Array<{pageNumber: number, text: string}>} pages - All document pages.
 * @returns {{ answer: string, citations: Array<{page: number, excerpt: string}>, cost: object }}
 */
async function askQuestion(question, pages) {
  // Build context: include page numbers so the model can cite them
  const documentContext = pages
    .map((p) => `[Page ${p.pageNumber}]\n${p.text}`)
    .join('\n\n---\n\n');

  const systemPrompt =
    'You are a precise document Q&A assistant. ' +
    'Answer the user\'s question based ONLY on the provided document. ' +
    'For every claim, cite the source page number(s) like [Page 3] or [Pages 4-5]. ' +
    'If the answer is not in the document, say "I couldn\'t find that in the document." ' +
    'Be concise but thorough. Include relevant quotes when helpful.';

  const userPrompt =
    `Here is the document content (with page numbers):\n\n${documentContext}\n\n---\n\nQuestion: ${question}`;

  // Call Ollama's chat API
  const response = await fetch(`${OLLAMA_HOST}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: MODEL,
      stream: false,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
    }),
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Ollama error (${response.status}): ${errText}`);
  }

  const data = await response.json();
  const answerText = data.message?.content || '';

  // Ollama returns token counts in the response
  const inputTokens = data.prompt_eval_count || 0;
  const outputTokens = data.eval_count || 0;

  totalInputTokens += inputTokens;
  totalOutputTokens += outputTokens;

  // Local models = free! Cost is always $0
  const sessionCost = 0;
  accumulatedCost = 0;

  // Parse page-number citations from answer
  const citations = extractCitations(answerText, pages);

  return {
    answer: answerText,
    citations,
    cost: {
      model: MODEL,
      inputTokens,
      outputTokens,
      sessionCost: 0,
      accumulatedCost: 0,
    },
  };
}

/**
 * Naively extract [Page N] citations from answer text and match them
 * to actual page excerpts.
 */
function extractCitations(answerText, pages) {
  const citationRegex = /\[Page(?:s)?\s*(\d+(?:\s*[–\-—,]\s*\d+)*)\]/gi;
  const citations = [];
  let match;

  while ((match = citationRegex.exec(answerText)) !== null) {
    const pageNums = match[1].match(/\d+/g);
    if (pageNums) {
      for (const num of pageNums) {
        const pageNum = parseInt(num, 10);
        const page = pages.find((p) => p.pageNumber === pageNum);
        if (page) {
          citations.push({
            page: pageNum,
            excerpt: page.text.slice(0, 250) + (page.text.length > 250 ? '...' : ''),
          });
        }
      }
    }
  }

  // Deduplicate by page number
  const seen = new Set();
  return citations.filter((c) => {
    if (seen.has(c.page)) return false;
    seen.add(c.page);
    return true;
  });
}

function getCostTelemetry() {
  return {
    model: MODEL,
    totalInputTokens,
    totalOutputTokens,
    accumulatedCost: 0,
  };
}

function resetCost() {
  accumulatedCost = 0;
  totalInputTokens = 0;
  totalOutputTokens = 0;
}

module.exports = { askQuestion, getCostTelemetry, resetCost };

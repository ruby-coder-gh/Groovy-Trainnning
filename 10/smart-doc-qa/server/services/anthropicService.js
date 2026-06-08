const Anthropic = require('@anthropic-ai/sdk');

// ---------------------------------------------------------------------------
// Pricing per 1M tokens (Claude 3 Haiku — good balance of speed & cost)
// https://www.anthropic.com/pricing
// ---------------------------------------------------------------------------
const PRICING = {
  haiku: { input: 0.25, output: 1.25 },   // per 1M tokens (USD)
  sonnet: { input: 3.00, output: 15.00 },
};

const MODEL = 'claude-3-haiku-20240307';
const activePricing = PRICING.haiku;

// Accumulated cost across all questions this session
let accumulatedCost = 0;
let totalInputTokens = 0;
let totalOutputTokens = 0;

const model = MODEL;

function createClient() {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error(
      'ANTHROPIC_API_KEY environment variable is not set.\n' +
      'Get your key at https://console.anthropic.com/ and export it:\n' +
      '  export ANTHROPIC_API_KEY=sk-ant-...'
    );
  }
  return new Anthropic({ apiKey });
}

/**
 * Ask a question about a document.
 * @param {string} question - The user's question.
 * @param {Array<{pageNumber: number, text: string}>} pages - All document pages.
 * @returns {{ answer: string, citations: Array<{page: number, excerpt: string}>, cost: object }}
 */
async function askQuestion(question, pages) {
  const client = createClient();

  // Build context: include page numbers so Claude can cite them
  const documentContext = pages
    .map((p) => `[Page ${p.pageNumber}]\n${p.text}`)
    .join('\n\n---\n\n');

  const systemPrompt =
    'You are a precise document Q&A assistant. ' +
    'Answer the user\'s question based ONLY on the provided document. ' +
    'For every claim, cite the source page number(s) like [Page 3] or [Pages 4-5]. ' +
    'If the answer is not in the document, say "I couldn\'t find that in the document." ' +
    'Be concise but thorough. Include relevant quotes when helpful.';

  const message = await client.messages.create({
    model,
    max_tokens: 4096,
    system: systemPrompt,
    messages: [
      {
        role: 'user',
        content: `Here is the document content (with page numbers):\n\n${documentContext}\n\n---\n\nQuestion: ${question}`,
      },
    ],
  });

  // Extract usage
  const inputTokens = message.usage.input_tokens;
  const outputTokens = message.usage.output_tokens;

  totalInputTokens += inputTokens;
  totalOutputTokens += outputTokens;

  const inputCost = (inputTokens / 1_000_000) * activePricing.input;
  const outputCost = (outputTokens / 1_000_000) * activePricing.output;
  const sessionCost = inputCost + outputCost;

  accumulatedCost += sessionCost;

  const answerText = message.content[0].text;

  // Parse page-number citations from answer
  const citations = extractCitations(answerText, pages);

  return {
    answer: answerText,
    citations,
    cost: {
      model,
      inputTokens,
      outputTokens,
      sessionCost: round(sessionCost),
      accumulatedCost: round(accumulatedCost),
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
          // Add a short excerpt from that page
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

function round(num) {
  return Math.round((num + Number.EPSILON) * 10000) / 10000;
}

function getCostTelemetry() {
  return {
    model,
    totalInputTokens,
    totalOutputTokens,
    accumulatedCost: round(accumulatedCost),
  };
}

function resetCost() {
  accumulatedCost = 0;
  totalInputTokens = 0;
  totalOutputTokens = 0;
}

module.exports = { askQuestion, getCostTelemetry, resetCost };

#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Day 7 / Week 2 Day 2 — Multi-Provider Benchmark
// Runs 50 prompts on Haiku · GPT-4o-mini · Gemini Flash
// Outputs a cost comparison table
//
// Usage:
//   export OPENAI_API_KEY=sk-...
//   export ANTHROPIC_API_KEY=sk-ant-...
//   export GEMINI_API_KEY=...
//   node benchmark.js
//
//   # Run only specific providers:
//   node benchmark.js --providers openai,gemini,anthropic
// ─────────────────────────────────────────────────────────────────────

"use strict";

// ─── Parse args ───────────────────────────────────────────────
const args = process.argv.slice(2);
const providersFlag = args.indexOf("--providers");
const PROVIDERS_FILTER = providersFlag !== -1 && args[providersFlag + 1]
  ? args[providersFlag + 1].split(",").map((s) => s.trim().toLowerCase())
  : ["openai", "gemini", "anthropic"];

// ─── 50 varied test prompts ─────────────────────────────────────
const PROMPTS = [
  // General knowledge / reasoning (1-10)
  "Explain the concept of recursion in programming with a simple example.",
  "What is the capital of Mongolia? What's an interesting fact about it?",
  "Write a haiku about machine learning.",
  "If a train leaves New York at 3 PM going 60 mph and another leaves Boston at 4 PM going 70 mph, when do they meet?",
  "List 5 best practices for writing clean Python code.",
  "What's the difference between symmetric and asymmetric encryption?",
  "Explain the water cycle in 3 sentences.",
  "What causes the Northern Lights?",
  "Write a SQL query to find duplicate emails in a users table.",
  "Convert the decimal number 255 to binary and hexadecimal.",

  // Creative writing (11-20)
  "Write a 2-sentence horror story set in a library.",
  "Compose a tweet announcing a new AI product called 'PromptPro'.",
  "Write a short product description for a smart water bottle.",
  "Create a slogan for a carbon-neutral delivery service.",
  "Write a limerick about debugging code.",
  "Describe the color blue to someone who has never seen it.",
  "Write a conversation between a cat and a smart speaker.",
  "Generate a rap verse about TypeScript vs JavaScript.",
  "Write a motivational quote for software engineers.",
  "Create a haiku about the internet.",

  // Code generation (21-30)
  "Write a Python function to check if a string is a palindrome.",
  "Create a React component that renders a countdown timer.",
  "Write a bash script to find and delete files older than 30 days.",
  "Write a JavaScript debounce function.",
  "Create a CSS animation for a loading spinner.",
  "Write a Python decorator that measures execution time.",
  "Generate a simple Express.js API endpoint for user registration.",
  "Write a SQL query to get the top 5 most ordered products.",
  "Create a Dockerfile for a Node.js application.",
  "Write a regular expression to validate an email address.",

  // Analysis / summarization (31-40)
  "Summarize the key differences between REST and GraphQL.",
  "Compare SQL vs NoSQL databases. When would you choose each?",
  "Explain the CAP theorem in simple terms.",
  "What are the pros and cons of microservices architecture?",
  "Compare React, Vue, and Angular for a new project.",
  "What is the difference between TCP and UDP?",
  "Explain how HTTPS works at a high level.",
  "Compare stateful vs stateless applications.",
  "What is the difference between unit testing and integration testing?",
  "Compare monolithic vs serverless architectures.",

  // Role-specific / domain (41-50)
  "You are a career coach. Give 3 tips for acending a technical interview.",
  "You are a nutritionist. Create a 1-day meal plan for a vegetarian athlete.",
  "You are a cybersecurity expert. List 5 ways to protect against phishing.",
  "You are a product manager. Write a PRD outline for a todo app.",
  "You are a DevOps engineer. Explain CI/CD pipeline stages.",
  "You are a data scientist. Explain overfitting and how to prevent it.",
  "You are a UX designer. List 5 heuristics for good UX.",
  "You are a tech founder. Write a pitch deck outline for an AI startup.",
  "You are a teacher. Explain binary search to a 10-year-old.",
  "You are a lawyer. List 3 things to consider before open-sourcing code.",
];

// ─── Provider SDKs (only needed if running that provider) ────────
const providers = {};

function initProviders() {
  if (PROVIDERS_FILTER.includes("openai")) {
    try {
      providers.openai = { sdk: require("openai"), model: "gpt-4o-mini" };
    } catch {
      console.warn("\x1b[33m⚠  openai SDK not installed. Run: npm install openai\x1b[0m");
    }
  }

  if (PROVIDERS_FILTER.includes("anthropic")) {
    try {
      providers.anthropic = { sdk: require("@anthropic-ai/sdk"), model: "claude-3-haiku-20240307" };
    } catch {
      console.warn("\x1b[33m⚠  @anthropic-ai/sdk not installed. Run: npm install @anthropic-ai/sdk\x1b[0m");
    }
  }

  if (PROVIDERS_FILTER.includes("gemini")) {
    try {
      providers.gemini = { sdk: require("@google/generative-ai"), model: "gemini-2.0-flash" };
    } catch {
      console.warn("\x1b[33m⚠  @google/generative-ai not installed. Run: npm install @google/generative-ai\x1b[0m");
    }
  }
}

// ─── OpenAI caller ───────────────────────────────────────────────
async function callOpenAI(prompt) {
  const openai = new providers.openai.sdk({ apiKey: process.env.OPENAI_API_KEY });
  const start = Date.now();
  const res = await openai.chat.completions.create({
    model: providers.openai.model,
    messages: [{ role: "user", content: prompt }],
    max_tokens: 500,
  });
  const elapsed = Date.now() - start;
  return {
    text: res.choices[0].message.content,
    usage: {
      in: res.usage?.prompt_tokens || 0,
      out: res.usage?.completion_tokens || 0,
    },
    latency: elapsed,
    model: providers.openai.model,
  };
}

// ─── Anthropic caller ────────────────────────────────────────────
async function callAnthropic(prompt) {
  const anthropic = new providers.anthropic.sdk({ apiKey: process.env.ANTHROPIC_API_KEY });
  const start = Date.now();
  const res = await anthropic.messages.create({
    model: providers.anthropic.model,
    max_tokens: 500,
    messages: [{ role: "user", content: prompt }],
  });
  const elapsed = Date.now() - start;
  return {
    text: res.content[0].text,
    usage: {
      in: res.usage?.input_tokens || 0,
      out: res.usage?.output_tokens || 0,
    },
    latency: elapsed,
    model: providers.anthropic.model,
  };
}

// ─── Gemini caller ───────────────────────────────────────────────
async function callGemini(prompt) {
  const { GoogleGenerativeAI } = providers.gemini.sdk;
  const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
  const model = genAI.getGenerativeModel({ model: providers.gemini.model });
  const start = Date.now();
  const result = await model.generateContent(prompt);
  const elapsed = Date.now() - start;
  const response = result.response;
  const usage = response.usageMetadata || {};
  return {
    text: response.text(),
    usage: {
      in: usage.promptTokenCount || 0,
      out: usage.candidatesTokenCount || 0,
    },
    latency: elapsed,
    model: providers.gemini.model,
  };
}

// ─── Cost rates (per 1M tokens, USD) ────────────────────────────
const COST_RATES = {
  "gpt-4o-mini": { in: 0.15, out: 0.60 },
  "claude-3-haiku-20240307": { in: 0.25, out: 1.25 },
  "gemini-2.0-flash": { in: 0.075, out: 0.30 },
};

function calcCost(model, usage) {
  const rates = COST_RATES[model];
  if (!rates) return 0;
  return (usage.in / 1_000_000) * rates.in + (usage.out / 1_000_000) * rates.out;
}

// ─── Runner ──────────────────────────────────────────────────────
async function runProvider(name, caller) {
  console.log(`\n\x1b[34m▶ Running ${name} (${providers[name].model}) — ${PROMPTS.length} prompts...\x1b[0m`);

  const results = [];
  let totalIn = 0;
  let totalOut = 0;
  let totalLatency = 0;
  let failures = 0;

  for (let i = 0; i < PROMPTS.length; i++) {
    const prompt = PROMPTS[i];
    process.stdout.write(
      `  [${i + 1}/${PROMPTS.length}] \x1b[90m${prompt.substring(0, 50).padEnd(52)}\x1b[0m`
    );

    try {
      const result = await caller(prompt);
      totalIn += result.usage.in;
      totalOut += result.usage.out;
      totalLatency += result.latency;
      results.push(result);
      const cost = calcCost(result.model, result.usage);
      process.stdout.write(
        ` ✓ \x1b[90m${result.usage.in} in · ${result.usage.out} out · ${(result.latency / 1000).toFixed(1)}s · \$${cost.toFixed(6)}\x1b[0m\n`
      );
    } catch (err) {
      failures++;
      process.stdout.write(` ✗ \x1b[31m${err.message.substring(0, 60)}\x1b[0m\n`);
    }

    // Small delay to avoid rate limits
    await new Promise((r) => setTimeout(r, 250));
  }

  const totalCost = calcCost(providers[name].model, { in: totalIn, out: totalOut });
  const avgLatency = totalLatency / (PROMPTS.length - failures);

  return {
    name,
    model: providers[name].model,
    prompts: PROMPTS.length,
    successes: PROMPTS.length - failures,
    failures,
    totalTokensIn: totalIn,
    totalTokensOut: totalOut,
    totalCost,
    avgLatency,
  };
}

// ─── Print table ─────────────────────────────────────────────────
function printTable(stats) {
  console.log("\n");
  console.log("\x1b[32m╔══════════════════════════════════════════════════════════════════════════════╗\x1b[0m");
  console.log("\x1b[32m║                     📊 Multi-Provider Benchmark — 50 Prompts                 ║\x1b[0m");
  console.log("\x1b[32m╚══════════════════════════════════════════════════════════════════════════════╝\x1b[0m");
  console.log("");

  // Header
  console.log(
    "\x1b[1m" +
    "  Provider        Model               Prompts  Success  Fail    Tokens In  Tokens Out   Total Cost    Avg Latency" +
    "\x1b[0m"
  );
  console.log(
    "  " +
    "─".repeat(100)
  );

  for (const s of stats) {
    const name = s.name.padEnd(16);
    const model = s.model.padEnd(20);
    const prompts = String(s.prompts).padStart(7);
    const success = String(s.successes).padStart(7);
    const fail = String(s.failures).padStart(5);
    const tokIn = String(s.totalTokensIn).padStart(11);
    const tokOut = String(s.totalTokensOut).padStart(11);
    const cost = `$${s.totalCost.toFixed(4)}`.padStart(12);
    const lat = `${(s.avgLatency / 1000).toFixed(1)}s`.padStart(12);

    console.log(`  ${name}${model}${prompts}${success}${fail}${tokIn}${tokOut}${cost}${lat}`);
  }

  console.log("");

  // Per-query cost breakdown
  console.log("\x1b[33m── Cost per query (50 prompts) ──\x1b[0m\n");
  for (const s of stats) {
    const perQuery = s.totalCost / s.successes;
    console.log(
      `  \x1b[36m${s.name.padEnd(12)}\x1b[0m  \$${perQuery.toFixed(5)}/query  ` +
      `(\$${(perQuery * 1000).toFixed(2)}/1000 queries)`
    );
  }

  console.log("");

  // Cost comparison ratios
  if (stats.length >= 2) {
    console.log("\x1b[33m── Cost ratio (vs cheapest) ──\x1b[0m\n");
    const cheapest = [...stats].sort((a, b) => a.totalCost - b.totalCost)[0];
    for (const s of stats) {
      const ratio = s.totalCost / cheapest.totalCost;
      const label = s === cheapest ? " ← cheapest" : "";
      console.log(
        `  \x1b[36m${s.name.padEnd(12)}\x1b[0m  ${ratio.toFixed(2)}x${label}`
      );
    }
  }

  console.log("");
}

// ─── Main ────────────────────────────────────────────────────────
async function main() {
  console.log("\x1b[32m🚀 Multi-Provider Benchmark — Day 7\x1b[0m");
  console.log(`   \x1b[90m${PROMPTS.length} prompts · Providers: ${PROVIDERS_FILTER.join(", ")}\x1b[0m`);
  console.log(`   \x1b[90mDate: ${new Date().toISOString().split("T")[0]}\x1b[0m\n`);

  initProviders();
  const stats = [];

  if (providers.openai && PROVIDERS_FILTER.includes("openai")) {
    stats.push(await runProvider("openai", callOpenAI));
  }

  if (providers.anthropic && PROVIDERS_FILTER.includes("anthropic")) {
    stats.push(await runProvider("anthropic", callAnthropic));
  }

  if (providers.gemini && PROVIDERS_FILTER.includes("gemini")) {
    stats.push(await runProvider("gemini", callGemini));
  }

  if (stats.length === 0) {
    console.log("\x1b[31mNo providers were available. Check API keys and SDK installations.\x1b[0m");
    return;
  }

  printTable(stats);
  console.log("\x1b[32m✅ Benchmark complete!\x1b[0m\n");
}

main().catch(console.error);

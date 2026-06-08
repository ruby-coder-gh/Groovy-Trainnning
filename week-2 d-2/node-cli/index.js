#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Day 7 / Week 2 Day 2 — Multi-Provider CLI Chatbot
// OpenAI · Gemini · Ollama  (switch via --provider flag)
//
// Usage:
//   node index.js                          # default: ollama
//   node index.js --provider openai
//   node index.js --provider gemini
//   node index.js --provider ollama
//   node index.js --model gpt-4o-mini      # override model
//
// Environment variables (optional per provider):
//   OPENAI_API_KEY    — required for OpenAI
//   GEMINI_API_KEY    — required for Gemini
// ─────────────────────────────────────────────────────────────────────

"use strict";

const readline = require("readline");

// ─── Parse CLI args ───────────────────────────────────────────────
const args = process.argv.slice(2);
const providerFlag = args.indexOf("--provider");
const modelFlag = args.indexOf("--model");

const PROVIDER = providerFlag !== -1 && args[providerFlag + 1]
  ? args[providerFlag + 1].toLowerCase()
  : "ollama";

const MODEL_OVERRIDE = modelFlag !== -1 && args[modelFlag + 1]
  ? args[modelFlag + 1]
  : null;

// ─── Provider configs ─────────────────────────────────────────────
const PROVIDERS = {
  openai: {
    name: "OpenAI",
    defaultModel: "gpt-4o-mini",
    url: "https://api.openai.com/v1/chat/completions",
    headers: () => ({
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.OPENAI_API_KEY || ""}`,
    }),
    // OpenAI uses 'user' / 'assistant' roles
    mapMessages: (msgs) => msgs,
    parseResponse: (data) => data.choices[0].message.content,
    parseUsage: (data) => data.usage
      ? { in: data.usage.prompt_tokens, out: data.usage.completion_tokens }
      : null,
    // gpt-4o-mini pricing per 1M tokens (as of 2025)
    costPer1MIn: 0.15,
    costPer1MOut: 0.60,
    // function calling example
    functions: [
      {
        name: "get_weather",
        description: "Get current weather for a city",
        parameters: {
          type: "object",
          properties: {
            city: { type: "string", description: "City name" },
            unit: { type: "string", enum: ["celsius", "fahrenheit"] },
          },
          required: ["city"],
        },
      },
    ],
  },

  gemini: {
    name: "Gemini",
    defaultModel: "gemini-2.0-flash",
    url: (model) =>
      `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${process.env.GEMINI_API_KEY || ""}`,
    headers: () => ({ "Content-Type": "application/json" }),
    // Gemini uses 'user' / 'model' roles (not 'assistant')
    mapMessages: (msgs) => ({
      contents: msgs.map((m) => ({
        role: m.role === "assistant" ? "model" : m.role,
        parts: [{ text: m.content }],
      })),
    }),
    parseResponse: (data) =>
      data.candidates?.[0]?.content?.parts?.[0]?.text || "(no response)",
    parseUsage: (data) => {
      if (data.usageMetadata) {
        return {
          in: data.usageMetadata.promptTokenCount,
          out: data.usageMetadata.candidatesTokenCount,
        };
      }
      return null;
    },
    // Gemini Flash pricing per 1M tokens
    costPer1MIn: 0.075,
    costPer1MOut: 0.30,
  },

  ollama: {
    name: "Ollama",
    defaultModel: "qwen3:8b",
    url: "http://localhost:11434/api/chat",
    headers: () => ({ "Content-Type": "application/json" }),
    mapMessages: (msgs) => ({ messages: msgs }),
    parseResponse: (data) => data.message?.content || "(no response)",
    parseUsage: (data) => {
      if (data.prompt_eval_count != null) {
        return { in: data.prompt_eval_count, out: data.eval_count };
      }
      return null;
    },
    // Free / local
    costPer1MIn: 0,
    costPer1MOut: 0,
  },
};

// ─── Validate ────────────────────────────────────────────────────
const provider = PROVIDERS[PROVIDER];
if (!provider) {
  console.error(
    `\x1b[31mUnknown provider: "${PROVIDER}". Use --provider openai | gemini | ollama\x1b[0m`
  );
  process.exit(1);
}

const MODEL = MODEL_OVERRIDE || provider.defaultModel;

if (PROVIDER === "openai" && !process.env.OPENAI_API_KEY) {
  console.warn(
    "\x1b[33m⚠  OPENAI_API_KEY not set. Set it via: export OPENAI_API_KEY=sk-...\x1b[0m"
  );
}

if (PROVIDER === "gemini" && !process.env.GEMINI_API_KEY) {
  console.warn(
    "\x1b[33m⚠  GEMINI_API_KEY not set. Set it via: export GEMINI_API_KEY=...\x1b[0m"
  );
}

// ─── Conversation history ────────────────────────────────────────
const messages = [];

// ─── Call provider API ───────────────────────────────────────────
async function callProvider(messages) {
  const url = typeof provider.url === "function"
    ? provider.url(MODEL)
    : provider.url;

  const body = provider.mapMessages(messages);

  // For OpenAI we include functions on first turn to demonstrate function calling
  if (PROVIDER === "openai") {
    body.model = MODEL;
    body.stream = false;
    // Attach function definitions
    if (provider.functions) {
      body.functions = provider.functions;
      body.function_call = "auto";
    }
  }

  const res = await fetch(url, {
    method: "POST",
    headers: provider.headers(),
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text().catch(() => "Unknown error");
    throw new Error(`${provider.name} API error ${res.status}: ${errText}`);
  }

  const data = await res.json();

  // Check for function call in OpenAI response
  if (PROVIDER === "openai") {
    const choice = data.choices?.[0];
    if (choice?.finish_reason === "function_call") {
      const fnCall = choice.message.function_call;
      const fnResult = await executeFunction(fnCall);
      // Append function call + result to messages, re-query
      messages.push({
        role: "assistant",
        content: null,
        function_call: { name: fnCall.name, arguments: fnCall.arguments },
      });
      messages.push({
        role: "function",
        name: fnCall.name,
        content: JSON.stringify(fnResult),
      });
      // Re-call without function definitions to get text response
      const { functions, ...bodyNoFn } = body;
      bodyNoFn.model = MODEL;
      bodyNoFn.stream = false;
      bodyNoFn.messages = messages.map((m) => {
        // strip function_call from user-facing response
        const { function_call, ...rest } = m;
        return m.role === "function" ? m : rest;
      });
      const res2 = await fetch(url, {
        method: "POST",
        headers: provider.headers(),
        body: JSON.stringify(bodyNoFn),
      });
      const data2 = await res2.json();
      return data2.choices[0].message.content;
    }
  }

  return provider.parseResponse(data);
}

// ─── Execute a function call (simulated) ─────────────────────────
async function executeFunction(fnCall) {
  const args = JSON.parse(fnCall.arguments);
  console.log(`\x1b[35m⚡ Function called: ${fnCall.name}(${JSON.stringify(args)})\x1b[0m`);

  if (fnCall.name === "get_weather") {
    // Simulated weather data
    const conditions = ["Sunny ☀️", "Cloudy ☁️", "Rainy 🌧️", "Windy 💨"];
    return {
      city: args.city,
      temperature: args.unit === "fahrenheit" ? 72 : 22,
      unit: args.unit || "celsius",
      condition: conditions[Math.floor(Math.random() * conditions.length)],
      humidity: `${Math.floor(Math.random() * 40 + 40)}%`,
    };
  }

  return { result: `Function ${fnCall.name} executed (simulated)` };
}

// ─── Get usage / cost ────────────────────────────────────────────
function formatCost(usage) {
  if (!usage) return "";
  const inCost = (usage.in / 1_000_000) * provider.costPer1MIn;
  const outCost = (usage.out / 1_000_000) * provider.costPer1MOut;
  const total = inCost + outCost;
  return ` [in: ${usage.in} · out: ${usage.out} · $${total.toFixed(6)}]`;
}

// ─── Chat loop ──────────────────────────────────────────────────
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: "\x1b[36mYou:\x1b[0m ",
});

let running = true;

async function chat() {
  rl.prompt();

  rl.on("line", async (input) => {
    const text = input.trim();

    if (text.toLowerCase() === "exit") {
      console.log("\n\x1b[32m👋 Bye!\x1b[0m");
      running = false;
      rl.close();
      return;
    }

    if (text.toLowerCase() === "/clear") {
      messages.length = 0;
      console.log("\x1b[33m🧹 History cleared.\x1b[0m\n");
      if (running) rl.prompt();
      return;
    }

    if (text.toLowerCase() === "/help") {
      console.log("");
      console.log("  \x1b[33mCommands:\x1b[0m");
      console.log("  \x1b[36mexit\x1b[0m        Exit the chatbot");
      console.log("  \x1b[36m/clear\x1b[0m      Clear conversation history");
      console.log("  \x1b[36m/help\x1b[0m       Show this help");
      if (PROVIDER === "openai") {
        console.log("  \x1b[36m/weather\x1b[0m    Try function calling (simulated weather)");
      }
      console.log("");
      if (running) rl.prompt();
      return;
    }

    // Special command for OpenAI function calling demo
    if (text.toLowerCase() === "/weather" && PROVIDER === "openai") {
      messages.push({
        role: "user",
        content: "What's the weather like in Tokyo and New York?",
      });
    } else {
      messages.push({ role: "user", content: text });
    }

    // Show thinking indicator
    process.stdout.write(`\x1b[33m${provider.name}:\x1b[0m `);

    try {
      const startTime = Date.now();
      const reply = await callProvider(messages);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

      console.log(reply);

      // Usage info (not available for simulated function calls)
      messages.push({ role: "assistant", content: reply });

      // Show token usage footer
      console.log(`\x1b[90m  ── ${provider.name} · ${MODEL} · ${elapsed}s\x1b[0m\n`);
    } catch (err) {
      console.log("");
      console.error(`\x1b[31m  ✗ Error:\x1b[0m ${err.message}\n`);
    }

    if (running) rl.prompt();
  });
}

// ─── Start banner ────────────────────────────────────────────────
console.log("");
console.log(`\x1b[32m╔══════════════════════════════════════════════╗\x1b[0m`);
console.log(`\x1b[32m║   🚀 Multi-Provider CLI Chatbot — Day 7     ║\x1b[0m`);
console.log(`\x1b[32m╚══════════════════════════════════════════════╝\x1b[0m`);
console.log(`  \x1b[36mProvider:\x1b[0m  ${provider.name}`);
console.log(`  \x1b[36mModel:\x1b[0m     ${MODEL}`);
console.log(`  \x1b[36mCost:\x1b[0m      ${provider.costPer1MIn === 0 ? "Free (local)" : `\$${provider.costPer1MIn}/1M in · \$${provider.costPer1MOut}/1M out`}`);
console.log(`  Type \x1b[31mexit\x1b[0m to quit · \x1b[31m/clear\x1b[0m to reset · \x1b[31m/help\x1b[0m for commands`);
if (PROVIDER === "openai") {
  console.log(`  Try \x1b[31m/weather\x1b[0m to see function calling in action`);
}
console.log("");

chat();

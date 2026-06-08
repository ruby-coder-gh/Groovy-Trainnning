#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Day 9 / Week 2 Day 4 — Codebase Explainer Tool
//
// Explains a codebase using an LLM, staying within 10K tokens per query.
// Uses Anthropic prompt caching when available for cost savings on
// repeated system prompts.
//
// Usage:
//   node explain.js <directory>                      # uses Claude (default)
//   node explain.js <directory> --provider openai
//   node explain.js <directory> --provider anthropic
//   node explain.js <directory> --max-tokens 5000
//   node explain.js <directory> --output summary.md
//   node explain.js <directory> --verbose
//
// Environment:
//   ANTHROPIC_API_KEY  — required for Anthropic/Claude
//   OPENAI_API_KEY     — required for OpenAI
// ─────────────────────────────────────────────────────────────────────

"use strict";

const fs = require("fs");
const path = require("path");

// ═════════════════════════════════════════════════════════════════════
// 1. CONFIG
// ═════════════════════════════════════════════════════════════════════

const args = process.argv.slice(2);
const targetDir = args.find((a) => !a.startsWith("--")) || ".";
const providerFlag = args.indexOf("--provider");
const PROVIDER = providerFlag !== -1 && args[providerFlag + 1]
  ? args[providerFlag + 1].toLowerCase()
  : "anthropic";

const MAX_TOKENS_PER_QUERY = parseInt(
  args[args.indexOf("--max-tokens") + 1] ||
  process.env.EXPLAIN_MAX_TOKENS ||
  "10000",
  10
);

const VERBOSE = args.includes("--verbose");
const OUTPUT_FILE = args[args.indexOf("--output") + 1] || null;

// ═════════════════════════════════════════════════════════════════════
// 2. TOOL: FILE SCANNER
// ═════════════════════════════════════════════════════════════════════

const IGNORED_DIRS = new Set([
  "node_modules", ".git", "dist", "build", ".next", "out",
  "__pycache__", ".cache", ".venv", "venv", "env", ".env",
  "coverage", ".nyc_output", ".turbo", ".tsbuildinfo",
]);

const SOURCE_EXTENSIONS = new Set([
  ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
  ".py", ".rb", ".go", ".rs", ".java", ".kt", ".swift",
  ".css", ".scss", ".less", ".html", ".htm", ".xml",
  ".json", ".yaml", ".yml", ".toml", ".md", ".sql",
  ".sh", ".bash", ".zsh", ".env.example", ".dockerfile",
  ".vue", ".svelte", ".astro",
]);

// Also explicitly look for common config files
const NAMED_FILES = new Set([
  "Dockerfile", "Makefile", "docker-compose.yml",
  "docker-compose.yaml", ".gitignore", ".env.example",
  "package.json", "tsconfig.json", "vite.config.js",
  "vite.config.ts", "next.config.js", "webpack.config.js",
  "requirements.txt", "Pipfile", "Gemfile", "Cargo.toml",
  "go.mod", "pom.xml", "build.gradle", "CMakeLists.txt",
]);

function scanDirectory(dirPath) {
  const files = [];

  function walk(currentPath) {
    let entries;
    try {
      entries = fs.readdirSync(currentPath, { withFileTypes: true });
    } catch {
      return; // skip unreadable
    }

    for (const entry of entries) {
      const fullPath = path.join(currentPath, entry.name);

      if (entry.isDirectory()) {
        if (!IGNORED_DIRS.has(entry.name) && !entry.name.startsWith(".")) {
          walk(fullPath);
        }
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();
        if (SOURCE_EXTENSIONS.has(ext) || NAMED_FILES.has(entry.name)) {
          files.push(fullPath);
        }
      }
    }
  }

  walk(path.resolve(dirPath));
  return files;
}

function estimateTokens(text) {
  return Math.ceil(text.length / 4);
}

function readFilesWithBudget(files, budgetTokens) {
  let totalTokens = 0;
  const results = [];

  for (const filePath of files) {
    let content;
    try {
      content = fs.readFileSync(filePath, "utf-8");
    } catch {
      continue; // skip unreadable
    }

    const fileTokens = estimateTokens(content);
    const relPath = path.relative(targetDir, filePath);

    if (totalTokens + fileTokens > budgetTokens) {
      // Truncate file to fit remaining budget
      const remainingTokens = budgetTokens - totalTokens;
      const maxChars = remainingTokens * 4;
      const truncated = content.slice(0, maxChars);
      results.push({
        path: relPath,
        content: truncated,
        truncated: true,
        tokens: remainingTokens,
      });
      totalTokens += remainingTokens;
      break;
    }

    results.push({
      path: relPath,
      content,
      truncated: false,
      tokens: fileTokens,
    });
    totalTokens += fileTokens;
  }

  return { files: results, totalTokens };
}

// ═════════════════════════════════════════════════════════════════════
// 3. LLM CALLER — Anthropic (with prompt caching) & OpenAI fallback
// ═════════════════════════════════════════════════════════════════════

const SYSTEM_PROMPT = `You are a senior software engineer reviewing a codebase. 
Your task is to explain what this codebase does, its architecture, key technologies, 
and notable patterns. Be concise but thorough. Focus on:
1. Overall purpose of the project
2. Tech stack and key dependencies
3. Architecture and component structure
4. Notable patterns, conventions, or design decisions
5. Entry points and how to run the project

Format your response in Markdown with clear sections.`;

async function callAnthropic(files, dirName) {
  const API_KEY = process.env.ANTHROPIC_API_KEY;
  if (!API_KEY) {
    throw new Error("ANTHROPIC_API_KEY not set");
  }

  // Build the code context
  let codeContext = `# Codebase: ${dirName}\n\n`;
  for (const f of files.files) {
    codeContext += `## File: ${f.path}\n\`\`\`\n${f.content}\n\`\`\`\n`;
    if (f.truncated) {
      codeContext += `\n*(file truncated to fit token budget)*\n`;
    }
  }

  const body = {
    model: "claude-sonnet-4-20250514",
    max_tokens: 4096,
    system: [
      {
        type: "text",
        text: SYSTEM_PROMPT,
        // Mark system prompt as cacheable for repeated use
        cache_control: { type: "ephemeral" },
      },
    ],
    messages: [
      {
        role: "user",
        content: [
          {
            type: "text",
            text: codeContext,
            // Mark the large code context as cacheable
            cache_control: { type: "ephemeral" },
          },
        ],
      },
    ],
  };

  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": API_KEY,
      "anthropic-version": "2023-06-01",
      "anthropic-beta": "prompt-caching-2024-07-31",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err.substring(0, 300)}`);
  }

  const data = await res.json();
  const text = data.content?.[0]?.text || "";

  // Extract cache metrics from response headers
  const cacheHit = res.headers.get("anthropic-cache-hit") || "unknown";
  const usage = data.usage || {};

  return {
    text,
    cacheHit,
    usage: {
      in: usage.input_tokens || 0,
      out: usage.output_tokens || 0,
      cacheCreation: usage.cache_creation_input_tokens || 0,
      cacheRead: usage.cache_read_input_tokens || 0,
    },
  };
}

async function callOpenAI(files, dirName) {
  const API_KEY = process.env.OPENAI_API_KEY;
  if (!API_KEY) {
    throw new Error("OPENAI_API_KEY not set");
  }

  let codeContext = `Codebase: ${dirName}\n\n`;
  for (const f of files.files) {
    codeContext += `File: ${f.path}\n\`\`\`\n${f.content}\n\`\`\`\n\n`;
    if (f.truncated) {
      codeContext += `*(truncated)*\n`;
    }
  }

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: codeContext },
      ],
      max_tokens: 4096,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`OpenAI API error ${res.status}: ${err.substring(0, 300)}`);
  }

  const data = await res.json();
  return {
    text: data.choices?.[0]?.message?.content || "",
    cacheHit: "n/a (OpenAI doesn't expose cache info)",
    usage: {
      in: data.usage?.prompt_tokens || 0,
      out: data.usage?.completion_tokens || 0,
      cacheCreation: 0,
      cacheRead: 0,
    },
  };
}

// ═════════════════════════════════════════════════════════════════════
// 4. MAIN
// ═════════════════════════════════════════════════════════════════════

async function main() {
  const resolvedDir = path.resolve(targetDir);
  const dirName = path.basename(resolvedDir);

  console.log(`\x1b[32m🔍 Codebase Explainer — Day 9\x1b[0m`);
  console.log(`   \x1b[36mDirectory:\x1b[0m  ${resolvedDir}`);
  console.log(`   \x1b[36mProvider:\x1b[0m   ${PROVIDER}`);
  console.log(`   \x1b[36mMax tokens:\x1b[0m ${MAX_TOKENS_PER_QUERY.toLocaleString()}\n`);

  // Scan
  console.log(`\x1b[36m📂 Scanning files...\x1b[0m`);
  const allFiles = scanDirectory(resolvedDir);
  console.log(`   Found ${allFiles.length} source files\n`);

  if (allFiles.length === 0) {
    console.log(`\x1b[33mNo source files found in ${resolvedDir}\x1b[0m`);
    return;
  }

  // Read within budget
  console.log(`\x1b[36m📖 Reading files (budget: ${MAX_TOKENS_PER_QUERY.toLocaleString()} tokens)...\x1b[0m`);
  const fileData = readFilesWithBudget(allFiles, MAX_TOKENS_PER_QUERY);

  console.log(`   Read ${fileData.files.length} files (${fileData.totalTokens.toLocaleString()} tokens)`);
  if (fileData.files.length < allFiles.length) {
    console.log(`   \x1b[33m   ${allFiles.length - fileData.files.length} files excluded to stay within budget\x1b[0m`);
  }

  // Show which files were included
  if (VERBOSE) {
    console.log("");
    console.log(`  \x1b[90mFiles included:\x1b[0m`);
    for (const f of fileData.files) {
      const flag = f.truncated ? " \x1b[33m(truncated)\x1b[0m" : "";
      console.log(`    \x1b[90m- ${f.path} (${f.tokens} tokens)${flag}\x1b[0m`);
    }
    console.log("");
  }

  // Call LLM
  console.log(`\x1b[36m🤖 Asking ${PROVIDER === "anthropic" ? "Claude (with prompt caching)" : "GPT-4o-mini"}...\x1b[0m\n`);

  const startTime = Date.now();
  let result;

  try {
    if (PROVIDER === "anthropic") {
      result = await callAnthropic(fileData, dirName);
    } else {
      result = await callOpenAI(fileData, dirName);
    }
  } catch (err) {
    console.error(`\x1b[31m✗ Error: ${err.message}\x1b[0m`);
    process.exit(1);
  }

  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

  // Output
  const output = result.text;

  // Print to console
  console.log(output);
  console.log("");

  // Show telemetry
  const inTokens = result.usage.in;
  const outTokens = result.usage.out;
  const providerCosts = {
    anthropic: { in: 3.0, out: 15.0 },   // claude-sonnet-4 pricing per 1M
    openai: { in: 0.15, out: 0.60 },     // gpt-4o-mini
  };
  const costs = providerCosts[PROVIDER] || providerCosts.openai;
  const cost = (inTokens / 1_000_000) * costs.in + (outTokens / 1_000_000) * costs.out;

  console.log(`\x1b[90m  ───────────────────────────────────────────────\x1b[0m`);
  console.log(`\x1b[90m  Provider:  ${PROVIDER}\x1b[0m`);
  console.log(`\x1b[90m  Tokens in: ${inTokens.toLocaleString()}\x1b[0m`);
  console.log(`\x1b[90m  Tokens out: ${outTokens.toLocaleString()}\x1b[0m`);
  console.log(`\x1b[90m  Cost:      \$${cost.toFixed(6)}\x1b[0m`);
  console.log(`\x1b[90m  Time:      ${elapsed}s\x1b[0m`);
  if (result.cacheHit) {
    const cacheIcon = result.cacheHit.includes("hit") ? "✅" : "❌";
    console.log(`\x1b[90m  Cache:     ${cacheIcon} ${result.cacheHit}\x1b[0m`);
  }
  console.log("");

  // Save to file if requested
  if (OUTPUT_FILE) {
    fs.writeFileSync(OUTPUT_FILE, output, "utf-8");
    console.log(`\x1b[32m✓ Saved explanation to ${OUTPUT_FILE}\x1b[0m\n`);
  }
}

main().catch(console.error);

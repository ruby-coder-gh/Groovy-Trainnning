#!/usr/bin/env node
// ─────────────────────────────────────────────────────────────────────
// Day 9 / Week 2 Day 4 — Token-Tracking Telemetry CSV Logger
//
// Logs every API call to a CSV file with full telemetry.
// Can be used standalone or imported as a module.
//
// Usage:
//   const telemetry = new Telemetry("telemetry.csv");
//   telemetry.log({ provider, model, promptTokens, completionTokens,
//                   cost, latencyMs, status, promptType, notes });
//   telemetry.summary();    // print summary to console
//   telemetry.close();      // flush & close
//
// CSV columns:
//   timestamp, provider, model, prompt_tokens, completion_tokens,
//   total_tokens, cost, latency_ms, status, prompt_type, notes
// ─────────────────────────────────────────────────────────────────────

"use strict";

const fs = require("fs");
const path = require("path");

const CSV_HEADER =
  "timestamp,provider,model,prompt_tokens,completion_tokens,total_tokens,cost,latency_ms,status,prompt_type,notes";

class Telemetry {
  /**
   * @param {string} filePath  Path to CSV file (default: ./telemetry.csv)
   * @param {boolean} verbose  Print each log entry to console
   */
  constructor(filePath = "./telemetry.csv", verbose = false) {
    this.filePath = path.resolve(filePath);
    this.verbose = verbose;
    this.logs = [];
    this._ensureHeader();
  }

  _ensureHeader() {
    const dir = path.dirname(this.filePath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    if (!fs.existsSync(this.filePath)) {
      fs.writeFileSync(this.filePath, CSV_HEADER + "\n", "utf-8");
    }
  }

  /**
   * Log a single API call to CSV and in-memory buffer.
   */
  log({
    provider = "unknown",
    model = "unknown",
    promptTokens = 0,
    completionTokens = 0,
    cost = 0,
    latencyMs = 0,
    status = "success",
    promptType = "general",
    notes = "",
  } = {}) {
    const timestamp = new Date().toISOString();
    const totalTokens = promptTokens + completionTokens;

    // Escape CSV fields (wrap in quotes if contains comma or quote)
    const esc = (v) => {
      const s = String(v);
      if (s.includes(",") || s.includes('"') || s.includes("\n")) {
        return `"${s.replace(/"/g, '""')}"`;
      }
      return s;
    };

    const row = [
      esc(timestamp),
      esc(provider),
      esc(model),
      promptTokens,
      completionTokens,
      totalTokens,
      cost.toFixed(8),
      latencyMs.toFixed(1),
      esc(status),
      esc(promptType),
      esc(notes),
    ].join(",");

    // Append to file
    fs.appendFileSync(this.filePath, row + "\n", "utf-8");

    // Store in memory for summary
    this.logs.push({
      timestamp,
      provider,
      model,
      promptTokens,
      completionTokens,
      totalTokens,
      cost,
      latencyMs,
      status,
      promptType,
      notes,
    });

    if (this.verbose) {
      const ink = `\x1b[36m${promptTokens}\x1b[0m`;
      const outk = `\x1b[33m${completionTokens}\x1b[0m`;
      console.log(
        `\x1b[90m[telemetry]\x1b[0m ${provider} · ${model} · ` +
        `in:${ink} out:${outk} · \$${cost.toFixed(6)} · ${latencyMs.toFixed(0)}ms · ${status}`
      );
    }
  }

  /**
   * Print a summary of all logged calls.
   */
  summary() {
    if (this.logs.length === 0) {
      console.log("\x1b[33mNo telemetry data logged yet.\x1b[0m");
      return;
    }

    const totalCalls = this.logs.length;
    const successful = this.logs.filter((l) => l.status === "success").length;
    const failed = totalCalls - successful;
    const totalTokens = this.logs.reduce((s, l) => s + l.totalTokens, 0);
    const totalCost = this.logs.reduce((s, l) => s + l.cost, 0);
    const totalLatency = this.logs.reduce((s, l) => s + l.latencyMs, 0);

    // Per-provider breakdown
    const byProvider = {};
    for (const l of this.logs) {
      if (!byProvider[l.provider]) {
        byProvider[l.provider] = { calls: 0, tokens: 0, cost: 0, latency: 0 };
      }
      byProvider[l.provider].calls++;
      byProvider[l.provider].tokens += l.totalTokens;
      byProvider[l.provider].cost += l.cost;
      byProvider[l.provider].latency += l.latencyMs;
    }

    console.log("");
    console.log("\x1b[32m╔════════════════════════════════════════════════╗\x1b[0m");
    console.log("\x1b[32m║     📊 Telemetry Dashboard — Session Summary  ║\x1b[0m");
    console.log("\x1b[32m╚════════════════════════════════════════════════╝\x1b[0m");
    console.log(`  \x1b[36mTotal calls:\x1b[0m   ${totalCalls} (${successful} OK, ${failed} failed)`);
    console.log(`  \x1b[36mTotal tokens:\x1b[0m  ${totalTokens.toLocaleString()} (${(totalTokens / 1_000_000).toFixed(2)}M)`);
    console.log(`  \x1b[36mTotal cost:\x1b[0m    \$${totalCost.toFixed(6)}`);
    console.log(`  \x1b[36mAvg latency:\x1b[0m   ${(totalLatency / totalCalls).toFixed(0)}ms`);
    console.log(`  \x1b[36mLog file:\x1b[0m      ${this.filePath}`);
    console.log("");

    console.log(`  \x1b[33m── Per-Provider Breakdown ──\x1b[0m\n`);
    for (const [prov, data] of Object.entries(byProvider)) {
      const avgLat = data.latency / data.calls;
      console.log(
        `  \x1b[36m${prov.padEnd(12)}\x1b[0m  ${data.calls} calls · ` +
        `${data.tokens.toLocaleString().padStart(8)} tokens · ` +
        `\$${data.cost.toFixed(4).padStart(8)} · ` +
        `${avgLat.toFixed(0)}ms avg`
      );
    }
    console.log("");

    // Bottom line
    const avgCostPerCall = totalCost / totalCalls;
    console.log(`  \x1b[33mAverage cost per call:\x1b[0m \$${avgCostPerCall.toFixed(6)}`);
    console.log(`  \x1b[33mProjected 10K calls:\x1b[0m  \$${(avgCostPerCall * 10000).toFixed(2)}`);
    console.log("");
  }

  /**
   * Close the telemetry (write final summary).
   */
  close() {
    this.summary();
  }
}

// ─── CLI Mode ──────────────────────────────────────────────────
// Run standalone: node logger.js <csv-path>
// Prints summary of existing CSV
if (require.main === module) {
  const filePath = process.argv[2] || "./telemetry.csv";
  const tel = new Telemetry(filePath);
  tel.summary();
}

module.exports = { Telemetry };

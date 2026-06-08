#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────
# Day 9 / Week 2 Day 4 — Token-Tracking Telemetry CSV Logger (Python)
#
# Logs every API call to a CSV file with full telemetry.
#
# Usage:
#   from logger import Telemetry
#   tel = Telemetry("telemetry.csv")
#   tel.log(provider="openai", model="gpt-4o-mini", prompt_tokens=100, ...)
#   tel.summary()
#
# CSV columns:
#   timestamp, provider, model, prompt_tokens, completion_tokens,
#   total_tokens, cost, latency_ms, status, prompt_type, notes
# ─────────────────────────────────────────────────────────────────────

import csv
import os
from datetime import datetime
from pathlib import Path


class Telemetry:
    """Logs API call telemetry to CSV and provides summary statistics."""

    def __init__(self, file_path="telemetry.csv", verbose=False):
        self.file_path = Path(file_path).resolve()
        self.verbose = verbose
        self.logs = []
        self._ensure_header()

    def _ensure_header(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            with open(self.file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "provider", "model", "prompt_tokens",
                    "completion_tokens", "total_tokens", "cost",
                    "latency_ms", "status", "prompt_type", "notes",
                ])

    def log(
        self,
        provider="unknown",
        model="unknown",
        prompt_tokens=0,
        completion_tokens=0,
        cost=0.0,
        latency_ms=0.0,
        status="success",
        prompt_type="general",
        notes="",
    ):
        """Log a single API call."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        total_tokens = prompt_tokens + completion_tokens

        row = [
            timestamp, provider, model, prompt_tokens,
            completion_tokens, total_tokens, round(cost, 8),
            round(latency_ms, 1), status, prompt_type, notes,
        ]

        # Append to CSV
        with open(self.file_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        # In-memory
        entry = {
            "timestamp": timestamp,
            "provider": provider,
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost": cost,
            "latency_ms": latency_ms,
            "status": status,
            "prompt_type": prompt_type,
            "notes": notes,
        }
        self.logs.append(entry)

        if self.verbose:
            print(
                f"\033[90m[telemetry]\033[0m {provider} · {model} · "
                f"in:{prompt_tokens} out:{completion_tokens} · "
                f"${cost:.6f} · {latency_ms:.0f}ms · {status}"
            )

        return entry

    def summary(self):
        """Print a full summary of all logged calls."""
        if not self.logs:
            print("\033[33mNo telemetry data logged yet.\033[0m")
            return

        total_calls = len(self.logs)
        successful = sum(1 for l in self.logs if l["status"] == "success")
        failed = total_calls - successful
        total_tok = sum(l["total_tokens"] for l in self.logs)
        total_cost = sum(l["cost"] for l in self.logs)
        total_lat = sum(l["latency_ms"] for l in self.logs)

        # Per-provider
        by_provider = {}
        for l in self.logs:
            p = l["provider"]
            if p not in by_provider:
                by_provider[p] = {"calls": 0, "tokens": 0, "cost": 0.0, "latency": 0.0}
            by_provider[p]["calls"] += 1
            by_provider[p]["tokens"] += l["total_tokens"]
            by_provider[p]["cost"] += l["cost"]
            by_provider[p]["latency"] += l["latency_ms"]

        print("")
        print("\033[32m╔════════════════════════════════════════════════╗\033[0m")
        print("\033[32m║     📊 Telemetry Dashboard — Session Summary  ║\033[0m")
        print("\033[32m╚════════════════════════════════════════════════╝\033[0m")
        print(f"  \033[36mTotal calls:\x1b[0m   {total_calls} ({successful} OK, {failed} failed)")
        print(f"  \033[36mTotal tokens:\x1b[0m  {total_tok:,} ({total_tok / 1_000_000:.2f}M)")
        print(f"  \033[36mTotal cost:\x1b[0m    ${total_cost:.6f}")
        print(f"  \033[36mAvg latency:\x1b[0m   {total_lat / total_calls:.0f}ms")
        print(f"  \033[36mLog file:\x1b[0m      {self.file_path}")
        print("")

        print("  \033[33m── Per-Provider Breakdown ──\033[0m\n")
        for prov, data in sorted(by_provider.items()):
            avg_lat = data["latency"] / data["calls"]
            print(
                f"  \033[36m{prov:12}\033[0m  {data['calls']} calls · "
                f"{data['tokens']:>8,} tokens · "
                f"${data['cost']:.4f} · "
                f"{avg_lat:.0f}ms avg"
            )

        print("")
        avg_cost = total_cost / total_calls
        print(f"  \033[33mAverage cost per call:\033[0m ${avg_cost:.6f}")
        print(f"  \033[33mProjected 10K calls:\033[0m  ${avg_cost * 10000:.2f}")
        print("")

    def close(self):
        self.summary()


if __name__ == "__main__":
    import sys
    file_path = sys.argv[1] if len(sys.argv) > 1 else "telemetry.csv"
    tel = Telemetry(file_path)
    tel.summary()

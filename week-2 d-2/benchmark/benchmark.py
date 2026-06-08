#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────
# Day 7 / Week 2 Day 2 — Multi-Provider Benchmark (Python)
# Runs 50 prompts on OpenAI · Gemini · (optionally Anthropic)
# Outputs a cost comparison table
#
# Usage:
#   export OPENAI_API_KEY=sk-...
#   export GEMINI_API_KEY=...
#   pip install openai google-generativeai
#   python benchmark.py
#
#   # Run only specific providers:
#   python benchmark.py --providers openai,gemini
# ─────────────────────────────────────────────────────────────────────

import json
import os
import sys
import time

# ─── Parse args ───────────────────────────────────────────────
PROVIDERS_FILTER = ["openai", "gemini"]

args = sys.argv[1:]
for i, arg in enumerate(args):
    if arg == "--providers" and i + 1 < len(args):
        PROVIDERS_FILTER = [p.strip().lower() for p in args[i + 1].split(",")]


# ─── 50 varied test prompts ─────────────────────────────────────
PROMPTS = [
    # General knowledge / reasoning (1-10)
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

    # Creative writing (11-20)
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

    # Code generation (21-30)
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

    # Analysis / summarization (31-40)
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

    # Role-specific / domain (41-50)
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
]


# ─── Cost rates (per 1M tokens, USD) ────────────────────────────
COST_RATES = {
    "gpt-4o-mini": {"in": 0.15, "out": 0.60},
    "gemini-2.0-flash": {"in": 0.075, "out": 0.30},
    "claude-3-haiku": {"in": 0.25, "out": 1.25},
}


def calc_cost(model, usage):
    rates = COST_RATES.get(model)
    if not rates:
        return 0
    return (usage["in"] / 1_000_000) * rates["in"] + (usage["out"] / 1_000_000) * rates["out"]


# ─── OpenAI caller ───────────────────────────────────────────────
def call_openai(prompt):
    import openai
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    start = time.time()
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    elapsed = time.time() - start
    usage = res.usage or {}
    return {
        "text": res.choices[0].message.content,
        "usage": {"in": usage.prompt_tokens or 0, "out": usage.completion_tokens or 0},
        "latency": elapsed,
        "model": "gpt-4o-mini",
    }


# ─── Gemini caller ───────────────────────────────────────────────
def call_gemini(prompt):
    import google.generativeai as genai
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")
    start = time.time()
    res = model.generate_content(prompt)
    elapsed = time.time() - start
    usage = {}
    try:
        usage = res.usage_metadata or {}
    except Exception:
        pass
    return {
        "text": res.text,
        "usage": {
            "in": getattr(usage, "prompt_token_count", 0) if not isinstance(usage, dict) else usage.get("promptTokenCount", 0),
            "out": getattr(usage, "candidates_token_count", 0) if not isinstance(usage, dict) else usage.get("candidatesTokenCount", 0),
        },
        "latency": elapsed,
        "model": "gemini-2.0-flash",
    }


# ─── Runner ──────────────────────────────────────────────────────
def run_provider(name, caller, model_name):
    print(f"\n\033[34m▶ Running {name} ({model_name}) — {len(PROMPTS)} prompts...\033[0m")

    total_in = 0
    total_out = 0
    total_latency = 0
    failures = 0

    for i, prompt in enumerate(PROMPTS, 1):
        sys.stdout.write(
            f"  [{i}/{len(PROMPTS)}] \033[90m{prompt[:50]:52}\033[0m"
        )
        sys.stdout.flush()

        try:
            result = caller(prompt)
            total_in += result["usage"]["in"]
            total_out += result["usage"]["out"]
            total_latency += result["latency"]
            cost = calc_cost(result["model"], result["usage"])
            sys.stdout.write(
                f" ✓ \033[90m{result['usage']['in']} in · {result['usage']['out']} out · "
                f"{result['latency']:.1f}s · ${cost:.6f}\033[0m\n"
            )
        except Exception as e:
            failures += 1
            sys.stdout.write(f" ✗ \033[31m{str(e)[:60]}\033[0m\n")

        sys.stdout.flush()
        time.sleep(0.25)  # rate limit courtesy

    total_cost = calc_cost(model_name, {"in": total_in, "out": total_out})
    successes = len(PROMPTS) - failures
    avg_latency = total_latency / successes if successes > 0 else 0

    return {
        "name": name,
        "model": model_name,
        "prompts": len(PROMPTS),
        "successes": successes,
        "failures": failures,
        "total_tokens_in": total_in,
        "total_tokens_out": total_out,
        "total_cost": total_cost,
        "avg_latency": avg_latency,
    }


# ─── Print table ─────────────────────────────────────────────────
def print_table(stats):
    print("\n")
    print("\033[32m╔══════════════════════════════════════════════════════════════════════════════╗\033[0m")
    print("\033[32m║                     📊 Multi-Provider Benchmark — 50 Prompts                 ║\033[0m")
    print("\033[32m╚══════════════════════════════════════════════════════════════════════════════╝\033[0m")
    print("")

    header = (
        f"  {'Provider':16} {'Model':20} {'Prompts':7} {'Success':7} {'Fail':5} "
        f"{'Tokens In':11} {'Tokens Out':11} {'Total Cost':12} {'Avg Latency':12}"
    )
    print(f"\033[1m{header}\033[0m")
    print(f"  {'─' * 100}")

    for s in stats:
        cost = f"${s['total_cost']:.4f}"
        lat = f"{s['avg_latency']:.1f}s"
        row = (
            f"  {s['name']:16} {s['model']:20} {s['prompts']:7} {s['successes']:7} {s['failures']:5} "
            f"{s['total_tokens_in']:11} {s['total_tokens_out']:11} {cost:>12} {lat:>12}"
        )
        print(row)

    print("")

    # Per-query cost
    print("\033[33m── Cost per query (50 prompts) ──\033[0m\n")
    for s in stats:
        per_query = s["total_cost"] / s["successes"] if s["successes"] > 0 else 0
        print(
            f"  \033[36m{s['name']:12}\033[0m  ${per_query:.5f}/query  "
            f"(${(per_query * 1000):.2f}/1000 queries)"
        )

    print("")

    # Cost ratio
    if len(stats) >= 2:
        print("\033[33m── Cost ratio (vs cheapest) ──\033[0m\n")
        cheapest = min(stats, key=lambda s: s["total_cost"])
        for s in stats:
            ratio = s["total_cost"] / cheapest["total_cost"]
            label = " ← cheapest" if s is cheapest else ""
            print(f"  \033[36m{s['name']:12}\033[0m  {ratio:.2f}x{label}")

    print("")


# ─── Main ────────────────────────────────────────────────────────
def main():
    print(f"\033[32m🚀 Multi-Provider Benchmark — Day 7\033[0m")
    print(f"   \033[90m{len(PROMPTS)} prompts · Providers: {', '.join(PROVIDERS_FILTER)}\033[0m")
    print(f"   \033[90mDate: {time.strftime('%Y-%m-%d')}\033[0m\n")

    stats = []

    if "openai" in PROVIDERS_FILTER:
        try:
            import openai
            stats.append(run_provider("OpenAI", call_openai, "gpt-4o-mini"))
        except ImportError:
            print("\033[33m⚠  openai SDK not installed. Run: pip install openai\033[0m")
        except Exception as e:
            print(f"\033[31m✗ Failed to initialize OpenAI: {e}\033[0m")

    if "gemini" in PROVIDERS_FILTER:
        try:
            import google.generativeai as genai
            stats.append(run_provider("Gemini", call_gemini, "gemini-2.0-flash"))
        except ImportError:
            print("\033[33m⚠  google-generativeai SDK not installed. Run: pip install google-generativeai\033[0m")
        except Exception as e:
            print(f"\033[31m✗ Failed to initialize Gemini: {e}\033[0m")

    if not stats:
        print("\033[31mNo providers were available. Check API keys and SDK installations.\033[0m")
        return

    print_table(stats)
    print("\033[32m✅ Benchmark complete!\033[0m\n")


if __name__ == "__main__":
    main()

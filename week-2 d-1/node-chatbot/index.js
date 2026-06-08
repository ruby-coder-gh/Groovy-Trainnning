// ──────────────────────────────────────────────────────────
// Anthropic CLI Chatbot — Node.js SDK
// Multi-turn conversation with history maintained
// ──────────────────────────────────────────────────────────

const Anthropic = require("@anthropic-ai/sdk");
const readline = require("readline");

const MODEL = "claude-sonnet-4-20250514";

// ─── Setup ───────────────────────────────────────────────
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: "\x1b[36mYou:\x1b[0m ",
});

// ─── Conversation history ────────────────────────────────
const messages = [];

// ─── Chat loop ──────────────────────────────────────────
async function chat() {
  rl.prompt();

  rl.on("line", async (input) => {
    const text = input.trim();

    if (text.toLowerCase() === "exit") {
      console.log("\n👋 Bye!");
      rl.close();
      return;
    }

    if (text.toLowerCase() === "/clear") {
      messages.length = 0;
      console.log("🧹 History cleared.\n");
      rl.prompt();
      return;
    }

    // Add user message to history
    messages.push({ role: "user", content: text });

    try {
      process.stdout.write("\x1b[33mClaude:\x1b[0m ");

      const response = await anthropic.messages.create({
        model: MODEL,
        max_tokens: 512,
        messages,
      });

      const reply = response.content[0].text;
      console.log(reply);

      // Add assistant response to history
      messages.push({ role: "assistant", content: reply });

      console.log(
        `\x1b[90m╰─ tokens: ${response.usage.input_tokens} in · ${response.usage.output_tokens} out\x1b[0m\n`
      );
    } catch (err) {
      console.error("\x1b[31mError:\x1b[0m", err.message);
    }

    rl.prompt();
  });
}

// ─── Start ───────────────────────────────────────────────
console.log("\n\x1b[32m🚀 Anthropic CLI Chatbot\x1b[0m");
console.log("   Model: " + MODEL);
console.log("   Type \x1b[31mexit\x1b[0m to quit · \x1b[31m/clear\x1b[0m to reset\n");

if (!process.env.ANTHROPIC_API_KEY) {
  console.error("❌ ANTHROPIC_API_KEY environment variable is required");
  process.exit(1);
}

chat();

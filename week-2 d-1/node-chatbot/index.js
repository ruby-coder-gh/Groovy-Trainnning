// ──────────────────────────────────────────────────────────
// Ollama CLI Chatbot — Node.js
// Multi-turn conversation with history maintained
// No external deps — uses built-in fetch (Node 18+)
// ──────────────────────────────────────────────────────────

const readline = require("readline");

const OLLAMA_URL = "http://localhost:11434/api/chat";
const MODEL = "qwen3:8b";

// ─── CLI Setup ───────────────────────────────────────────
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  prompt: "\x1b[36mYou:\x1b[0m ",
});

// ─── Conversation history ────────────────────────────────
const messages = [];
let running = true;

// ─── Call Ollama ─────────────────────────────────────────
async function askOllama(messages) {
  const res = await fetch(OLLAMA_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: MODEL, messages, stream: false }),
  });
  const data = await res.json();
  return data.message.content;
}

// ─── Chat loop ──────────────────────────────────────────
async function chat() {
  rl.prompt();

  rl.on("line", async (input) => {
    const text = input.trim();

    if (text.toLowerCase() === "exit") {
      console.log("\n👋 Bye!");
      running = false;
      rl.close();
      return;
    }

    if (text.toLowerCase() === "/clear") {
      messages.length = 0;
      console.log("🧹 History cleared.\n");
      if (running) rl.prompt();
      return;
    }

    messages.push({ role: "user", content: text });

    try {
      process.stdout.write("\x1b[33mOllama:\x1b[0m ");
      const reply = await askOllama(messages);
      console.log(reply);
      messages.push({ role: "assistant", content: reply });
      console.log("");
    } catch (err) {
      console.error("\x1b[31mError:\x1b[0m", err.message);
    }

    if (running) rl.prompt();
  });
}

// ─── Start ───────────────────────────────────────────────
console.log("\n\x1b[32m🚀 Ollama CLI Chatbot\x1b[0m");
console.log(`   Model: ${MODEL}`);
console.log("   Type \x1b[31mexit\x1b[0m to quit · \x1b[31m/clear\x1b[0m to reset\n");

chat();

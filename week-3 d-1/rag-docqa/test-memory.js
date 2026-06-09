#!/usr/bin/env node
// Memory monitoring wrapper for server.js
"use strict";

const origLog = console.log;
const memInterval = setInterval(() => {
  const m = process.memoryUsage();
  origLog(`[mem-mon] rss=${(m.rss / 1024 / 1024).toFixed(0)}MB heap=${(m.heapUsed / 1024 / 1024).toFixed(0)}/${(m.heapTotal / 1024 / 1024).toFixed(0)}MB ext=${(m.external / 1024 / 1024).toFixed(0)}MB`);
}, 3000);

// Load the server
require("./server.js");

// Keep process alive
process.on("SIGINT", () => {
  clearInterval(memInterval);
  process.exit(0);
});

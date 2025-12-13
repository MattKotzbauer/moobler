#!/usr/bin/env bun
import { render } from "ink";
import { App } from "./app.js";

// Enter alternate screen buffer (like vim, htop, claude code)
process.stdout.write("\x1b[?1049h"); // Enter alt screen
process.stdout.write("\x1b[2J");     // Clear screen
process.stdout.write("\x1b[H");      // Move cursor to top-left

// Restore terminal on exit
const cleanup = () => {
  process.stdout.write("\x1b[?1049l"); // Exit alt screen
};

process.on("exit", cleanup);
process.on("SIGINT", () => {
  cleanup();
  process.exit(0);
});
process.on("SIGTERM", () => {
  cleanup();
  process.exit(0);
});

const { unmount, waitUntilExit } = render(<App />, {
  exitOnCtrlC: false,
});

await waitUntilExit();

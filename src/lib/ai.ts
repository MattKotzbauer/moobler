import Anthropic from "@anthropic-ai/sdk";
import { readTmuxConfig, type UserStyle } from "./config.js";
import { scrapeGitHubConfigs } from "./github.js";
import { join } from "path";

export interface KeybindSuggestion {
  keybind: string;
  command: string;
  description: string;
}

export interface KeybindGroup {
  name: string;
  description: string;
  keybinds: KeybindSuggestion[];
  reasoning: string;
}

export interface SuggestionResult {
  styleAnalysis: {
    prefixPreference: string;
    modifierPreference: string;
    navigationStyle: string;
    keysInUse: string[];
  } | null;
  groups: KeybindGroup[];
}

export type ProgressCallback = (status: string) => void;

// Load prompts from files
const PROMPTS_DIR = join(import.meta.dir, "../prompts");

async function loadPrompt(name: string): Promise<string> {
  const path = join(PROMPTS_DIR, `${name}.txt`);
  return await Bun.file(path).text();
}

function interpolate(template: string, vars: Record<string, string>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key) => vars[key] ?? "");
}

/**
 * Sanitize keybind string - AI sometimes adds trailing colons or spaces
 */
function sanitizeKeybind(keybind: string): string {
  return keybind
    .trim()
    .replace(/:+$/, "")  // Remove trailing colons
    .replace(/\s+$/, ""); // Remove trailing spaces
}

/**
 * Sanitize command string - fix common AI output issues
 */
function sanitizeCommand(command: string): string {
  return command
    .trim()
    .replace(/^["']|["']$/g, "")  // Remove wrapping quotes
    .replace(/\\;/g, " \\; ")     // Ensure proper spacing around escaped semicolons
    .replace(/\s+/g, " ")         // Normalize whitespace
    .trim();
}

/**
 * Validate that a keybind looks syntactically correct
 */
function isValidKeybind(kb: { keybind: string; command: string }): boolean {
  // Keybind should not be empty
  if (!kb.keybind || kb.keybind.length === 0) return false;

  // Command should not be empty
  if (!kb.command || kb.command.length === 0) return false;

  // Keybind should not contain spaces (except for special keys like "Space")
  if (kb.keybind.includes(" ") && kb.keybind !== "Space") return false;

  // Command should start with a valid tmux command
  const validCommands = [
    "select-", "resize-", "split-", "swap-", "kill-", "new-", "next-", "prev-",
    "last-", "send-", "copy-", "paste-", "set-", "display-", "list-", "source-",
    "run-", "if-", "command-prompt", "choose-", "break-", "join-", "move-",
    "rename-", "rotate-", "switch-", "detach", "attach", "has-", "show-",
    "bind", "unbind", "refresh", "clear", "clock", "confirm", "suspend",
    "lock", "pipe", "wait", "load", "save", "delete"
  ];

  const firstWord = kb.command.split(/\s/)[0];
  const isValid = validCommands.some(cmd => firstWord.startsWith(cmd));

  return isValid;
}

export async function getAISuggestions(
  category?: string,
  onProgress?: ProgressCallback
): Promise<SuggestionResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY not set");
  }

  const client = new Anthropic({ apiKey });

  // Progress updates
  onProgress?.("Loading prompts...");

  // Load prompts
  const systemPrompt = await loadPrompt("suggestions-system");
  const userPromptTemplate = await loadPrompt("suggestions-user");

  onProgress?.("Reading your tmux config...");

  // Read user's config
  const userConfig = await readTmuxConfig();

  onProgress?.("Scraping GitHub configs for inspiration...");

  // Fetch GitHub configs for inspiration
  let githubKeybinds = "";
  try {
    const scraped = await scrapeGitHubConfigs();
    githubKeybinds = scraped
      .slice(0, 30)
      .map((kb) => `  ${kb.raw} (from ${kb.source})`)
      .join("\n");
    onProgress?.(`Found ${scraped.length} keybinds from GitHub...`);
  } catch {
    githubKeybinds = "GitHub configs unavailable";
    onProgress?.("GitHub unavailable, using local data...");
  }

  const categoryFocus = category
    ? `\nFocus specifically on ${category} keybindings.`
    : "";

  const userPrompt = interpolate(userPromptTemplate, {
    userConfig: userConfig || "No existing tmux.conf found - user is starting fresh",
    githubKeybinds,
    categoryFocus,
  });

  onProgress?.("Asking Claude for suggestions...");

  // Use streaming for progress updates
  let fullText = "";
  const stream = client.messages.stream({
    model: "claude-sonnet-4-20250514",
    max_tokens: 2048,
    system: systemPrompt,
    messages: [{ role: "user", content: userPrompt }],
  });

  // Show streaming progress
  let lastUpdate = Date.now();
  stream.on("text", (text) => {
    fullText += text;
    // Throttle updates to every 500ms
    if (Date.now() - lastUpdate > 500) {
      // Try to extract what Claude is thinking about
      const lines = fullText.split("\n").filter(l => l.trim());
      const lastLine = lines[lines.length - 1] || "";
      if (lastLine.includes('"name"')) {
        const match = lastLine.match(/"name"\s*:\s*"([^"]+)"/);
        if (match) {
          onProgress?.(`Generating: ${match[1]}...`);
        }
      } else if (fullText.length < 200) {
        onProgress?.("Analyzing your style preferences...");
      } else {
        onProgress?.(`Generating suggestions (${Math.floor(fullText.length / 100)}%)...`);
      }
      lastUpdate = Date.now();
    }
  });

  await stream.finalMessage();

  onProgress?.("Parsing suggestions...");

  // Extract JSON from response
  let jsonText = fullText;
  const jsonMatch = fullText.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
  if (jsonMatch) {
    jsonText = jsonMatch[1];
  }

  try {
    const data = JSON.parse(jsonText);

    const styleAnalysis = data.user_style_analysis
      ? {
          prefixPreference: data.user_style_analysis.prefix_preference,
          modifierPreference: data.user_style_analysis.modifier_preference,
          navigationStyle: data.user_style_analysis.navigation_style,
          keysInUse: data.user_style_analysis.keys_in_use || [],
        }
      : null;

    const groups: KeybindGroup[] = (data.groups || []).map((g: any) => {
      // Sanitize and validate keybinds
      const sanitizedKeybinds = (g.keybinds || [])
        .map((kb: any) => ({
          keybind: sanitizeKeybind(kb.keybind || ""),
          command: sanitizeCommand(kb.command || ""),
          description: kb.description || "",
        }))
        .filter(isValidKeybind);

      return {
        name: g.name || "Suggestions",
        description: g.description || "",
        keybinds: sanitizedKeybinds,
        reasoning: g.reasoning || "",
      };
    }).filter(g => g.keybinds.length > 0);  // Remove empty groups

    onProgress?.("Done!");
    return { styleAnalysis, groups };
  } catch {
    return {
      styleAnalysis: null,
      groups: [
        {
          name: "AI Suggestions",
          description: "Could not parse response",
          keybinds: [],
          reasoning: fullText,
        },
      ],
    };
  }
}

export async function generateChallenge(
  keybind: string,
  command: string
): Promise<{ objective: string; hint: string }> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return {
      objective: `Practice using ${keybind}`,
      hint: `This executes: ${command}`,
    };
  }

  const client = new Anthropic({ apiKey });

  // Load and interpolate prompt
  const promptTemplate = await loadPrompt("challenge");
  const prompt = interpolate(promptTemplate, { keybind, command });

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [{ role: "user", content: prompt }],
  });

  const text =
    response.content[0].type === "text" ? response.content[0].text : "";

  try {
    const match = text.match(/\{[\s\S]*\}/);
    if (match) {
      return JSON.parse(match[0]);
    }
  } catch {}

  return {
    objective: `Practice using ${keybind}`,
    hint: `This executes: ${command}`,
  };
}

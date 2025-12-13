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

// Load prompts from files
const PROMPTS_DIR = join(import.meta.dir, "../prompts");

async function loadPrompt(name: string): Promise<string> {
  const path = join(PROMPTS_DIR, `${name}.txt`);
  return await Bun.file(path).text();
}

function interpolate(template: string, vars: Record<string, string>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, key) => vars[key] ?? "");
}

export async function getAISuggestions(
  category?: string
): Promise<SuggestionResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY not set");
  }

  const client = new Anthropic({ apiKey });

  // Load prompts
  const systemPrompt = await loadPrompt("suggestions-system");
  const userPromptTemplate = await loadPrompt("suggestions-user");

  // Read user's config
  const userConfig = await readTmuxConfig();

  // Fetch GitHub configs for inspiration
  let githubKeybinds = "";
  try {
    const scraped = await scrapeGitHubConfigs();
    githubKeybinds = scraped
      .slice(0, 30)
      .map((kb) => `  ${kb.raw} (from ${kb.source})`)
      .join("\n");
  } catch {
    githubKeybinds = "GitHub configs unavailable";
  }

  const categoryFocus = category
    ? `\nFocus specifically on ${category} keybindings.`
    : "";

  const userPrompt = interpolate(userPromptTemplate, {
    userConfig: userConfig || "No existing tmux.conf found - user is starting fresh",
    githubKeybinds,
    categoryFocus,
  });

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 2048,
    system: systemPrompt,
    messages: [{ role: "user", content: userPrompt }],
  });

  const text =
    response.content[0].type === "text" ? response.content[0].text : "";

  // Extract JSON from response
  let jsonText = text;
  const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)\s*```/);
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

    const groups: KeybindGroup[] = (data.groups || []).map((g: any) => ({
      name: g.name || "Suggestions",
      description: g.description || "",
      keybinds: g.keybinds || [],
      reasoning: g.reasoning || "",
    }));

    return { styleAnalysis, groups };
  } catch {
    return {
      styleAnalysis: null,
      groups: [
        {
          name: "AI Suggestions",
          description: "Could not parse response",
          keybinds: [],
          reasoning: text,
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

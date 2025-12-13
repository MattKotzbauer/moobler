import Anthropic from "@anthropic-ai/sdk";
import { readTmuxConfig, type UserStyle } from "./config.js";
import { scrapeGitHubConfigs } from "./github.js";

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

const SYSTEM_PROMPT = `You are a tmux expert helping users discover new keybindings.

STEP 1 - ANALYZE USER'S STYLE PATTERNS (do this carefully before suggesting anything):

Look at their config and determine:
1. **Prefix vs No-Prefix preference**:
   - Count bindings using \`bind -n\` (no prefix, direct shortcuts) vs \`bind\` (requires prefix)
   - If they predominantly use \`bind -n M-...\` (Alt+key), they prefer PREFIX-FREE bindings
   - If they mostly use \`bind X ...\` (prefix then key), they prefer PREFIX bindings
   - MATCH THEIR PREFERENCE. If they use Alt for everything, suggest Alt bindings.

2. **Modifier preference**:
   - Do they use M- (Alt/Meta) bindings?
   - Do they use C- (Ctrl) bindings?
   - Do they use Shift variants (uppercase like M-H vs M-h)?

3. **Navigation style**:
   - vim keys (h/j/k/l)?
   - arrow keys?
   - other patterns?

4. **Keys already in use**: List ALL keys they've bound so you don't conflict

STEP 2 - SUGGEST COMPLEMENTARY KEYBINDINGS:

Your suggestions MUST:
- Use the SAME binding style as the user (if they use M-x everywhere, suggest M-x bindings)
- Fill gaps in their config (e.g., if they have M-hjkl for nav, suggest M-HJKL for resize)
- NOT conflict with their existing bindings
- NOT conflict with universal terminal keys (C-c, C-d, C-z, C-s, C-q, C-l, C-a)

CRITICAL: If the user's config shows they avoid the prefix key and use Alt/Meta bindings
instead, DO NOT suggest prefix bindings. Suggest Alt/Meta bindings that complement their setup.

STEP 3 - GROUP LOGICALLY:
- Group related keybindings (e.g., all 4 resize directions together)
- Each group should be something to practice in one session

KEYBIND FORMAT - USE EXACT TMUX SYNTAX:
- For prefix bindings: just the key after prefix, e.g. "r" (user presses prefix then r)
- For no-prefix bindings: include the modifier, e.g. "M-h" (Alt+h with no prefix)
- NEVER write "prefix X" - that's documentation notation, not tmux syntax
- Examples of CORRECT format: "M-h", "M-J", "r", "C-s", "|", "-"
- Examples of WRONG format: "prefix r", "prefix C-f", "Prefix+r"

Respond in JSON format with this structure:
{
  "user_style_analysis": {
    "prefix_preference": "no-prefix (Alt/Meta)" | "prefix-based" | "mixed",
    "modifier_preference": "Alt/Meta" | "Ctrl" | "mixed",
    "navigation_style": "vim" | "arrows" | "other",
    "keys_in_use": ["M-h", "M-j", "M-k", "M-l", ...]
  },
  "groups": [
    {
      "name": "Group Name",
      "description": "What this group of keybinds does",
      "keybinds": [
        {"keybind": "M-H", "command": "resize-pane -L 5", "description": "Resize pane left"},
        {"keybind": "M-J", "command": "resize-pane -D 5", "description": "Resize pane down"}
      ],
      "reasoning": "Why these bindings complement the user's existing style"
    }
  ]
}

Return 2-4 groups of suggestions that MATCH the user's established patterns.`;

export async function getAISuggestions(
  category?: string
): Promise<SuggestionResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    throw new Error("ANTHROPIC_API_KEY not set");
  }

  const client = new Anthropic({ apiKey });

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

  const userPrompt = `Here is the user's current tmux configuration:

\`\`\`
${userConfig || "No existing tmux.conf found - user is starting fresh"}
\`\`\`

Here are popular keybindings from GitHub configs (use as inspiration, ADAPT to user's style):

${githubKeybinds}
${categoryFocus}

IMPORTANT: First analyze the user's config to identify their patterns:
- Do they use \`bind -n\` (no prefix) or \`bind\` (with prefix)?
- What modifiers do they prefer (M- for Alt, C- for Ctrl)?
- What keys are already taken?

Then suggest keybindings that use the SAME style. If they use Alt+key bindings everywhere,
suggest more Alt+key bindings - NOT prefix bindings.

Return valid JSON with user_style_analysis and groups.`;

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 2048,
    system: SYSTEM_PROMPT,
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

  const response = await client.messages.create({
    model: "claude-sonnet-4-20250514",
    max_tokens: 256,
    messages: [
      {
        role: "user",
        content: `Create a brief practice challenge for tmux keybind "${keybind}" which does "${command}".
Return JSON: {"objective": "...", "hint": "..."}`,
      },
    ],
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

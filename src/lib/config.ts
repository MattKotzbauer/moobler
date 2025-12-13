import { homedir } from "os";
import { join } from "path";

export interface Keybinding {
  key: string;
  command: string;
  mode: "prefix" | "root";
  raw: string;
}

export interface UserStyle {
  prefixPreference: "no-prefix" | "prefix-based" | "mixed";
  modifierPreference: "Alt/Meta" | "Ctrl" | "mixed";
  navigationStyle: "vim" | "arrows" | "other";
  keysInUse: string[];
}

export interface TmuxConfig {
  keybindings: Keybinding[];
  style: UserStyle;
  raw: string;
}

export async function readTmuxConfig(): Promise<string> {
  const configPath = join(homedir(), ".tmux.conf");
  try {
    return await Bun.file(configPath).text();
  } catch {
    return "";
  }
}

export function parseTmuxConfig(content: string): TmuxConfig {
  const keybindings: Keybinding[] = [];
  const lines = content.split("\n");

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    // Match bind/bind-key commands
    const match = trimmed.match(/^(?:bind-key|bind)\s+(.+)$/);
    if (!match) continue;

    let args = match[1];
    let mode: "prefix" | "root" = "prefix";

    // Check for -n flag (root/no-prefix binding)
    if (args.startsWith("-n ")) {
      mode = "root";
      args = args.slice(3);
    }

    // Handle -T flag
    if (args.startsWith("-T ")) {
      args = args.replace(/^-T\s+\S+\s+/, "");
    }

    // Split into key and command
    const parts = args.split(/\s+/);
    if (parts.length < 2) continue;

    const key = parts[0];
    const command = parts.slice(1).join(" ");

    keybindings.push({ key, command, mode, raw: trimmed });
  }

  // Analyze style
  const style = analyzeStyle(keybindings);

  return { keybindings, style, raw: content };
}

function analyzeStyle(bindings: Keybinding[]): UserStyle {
  const rootBindings = bindings.filter((b) => b.mode === "root");
  const prefixBindings = bindings.filter((b) => b.mode === "prefix");
  const keysInUse = bindings.map((b) => (b.mode === "root" ? b.key : `prefix+${b.key}`));

  // Prefix preference
  let prefixPreference: UserStyle["prefixPreference"];
  if (rootBindings.length === 0) {
    prefixPreference = "prefix-based";
  } else if (prefixBindings.length === 0) {
    prefixPreference = "no-prefix";
  } else if (rootBindings.length > prefixBindings.length) {
    prefixPreference = "no-prefix";
  } else if (rootBindings.length < prefixBindings.length / 2) {
    prefixPreference = "prefix-based";
  } else {
    prefixPreference = "mixed";
  }

  // Modifier preference
  const altBindings = bindings.filter((b) => b.key.startsWith("M-"));
  const ctrlBindings = bindings.filter((b) => b.key.startsWith("C-"));
  let modifierPreference: UserStyle["modifierPreference"];
  if (altBindings.length > ctrlBindings.length * 2) {
    modifierPreference = "Alt/Meta";
  } else if (ctrlBindings.length > altBindings.length * 2) {
    modifierPreference = "Ctrl";
  } else {
    modifierPreference = "mixed";
  }

  // Navigation style
  const hasVimKeys = bindings.some(
    (b) =>
      b.key === "h" ||
      b.key === "j" ||
      b.key === "k" ||
      b.key === "l" ||
      b.key === "M-h" ||
      b.key === "M-j" ||
      b.key === "M-k" ||
      b.key === "M-l"
  );
  const hasArrowKeys = bindings.some(
    (b) =>
      b.key === "Up" ||
      b.key === "Down" ||
      b.key === "Left" ||
      b.key === "Right"
  );
  let navigationStyle: UserStyle["navigationStyle"];
  if (hasVimKeys) {
    navigationStyle = "vim";
  } else if (hasArrowKeys) {
    navigationStyle = "arrows";
  } else {
    navigationStyle = "other";
  }

  return {
    prefixPreference,
    modifierPreference,
    navigationStyle,
    keysInUse,
  };
}

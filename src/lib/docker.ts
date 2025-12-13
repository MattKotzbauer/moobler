import Docker from "dockerode";
import { homedir } from "os";
import { join } from "path";
import { tmpdir } from "os";
import { writeFile, unlink } from "fs/promises";
import { platform } from "os";

export type TerminalType = "kitty" | "ghostty" | "iterm2" | "gnome-terminal" | "unknown";

/**
 * Detect the current terminal emulator using environment variables
 */
export function detectTerminal(): TerminalType {
  // Kitty sets KITTY_WINDOW_ID
  if (process.env.KITTY_WINDOW_ID) {
    return "kitty";
  }

  // Ghostty sets GHOSTTY_RESOURCES_DIR or TERM_PROGRAM=ghostty
  if (process.env.GHOSTTY_RESOURCES_DIR || process.env.TERM_PROGRAM === "ghostty") {
    return "ghostty";
  }

  // iTerm2 sets TERM_PROGRAM=iTerm.app or ITERM_SESSION_ID
  if (process.env.TERM_PROGRAM === "iTerm.app" || process.env.ITERM_SESSION_ID) {
    return "iterm2";
  }

  // GNOME Terminal sets GNOME_TERMINAL_SCREEN or VTE_VERSION
  if (process.env.GNOME_TERMINAL_SCREEN || process.env.VTE_VERSION) {
    return "gnome-terminal";
  }

  return "unknown";
}

/**
 * Check if a terminal binary is available
 */
async function hasTerminal(name: string): Promise<boolean> {
  const proc = Bun.spawn(["which", name]);
  await proc.exited;
  return proc.exitCode === 0;
}

const docker = new Docker();
const IMAGE_NAME = "tmux-learn-sandbox";
const CONTAINER_NAME = "tmux-sandbox";
const PREWARM_NAME = "moobler-prewarm";

export async function isDockerAvailable(): Promise<boolean> {
  try {
    await docker.ping();
    return true;
  } catch {
    return false;
  }
}

export async function isImageBuilt(): Promise<boolean> {
  try {
    await docker.getImage(IMAGE_NAME).inspect();
    return true;
  } catch {
    return false;
  }
}

export async function buildImage(): Promise<void> {
  const dockerfilePath = join(import.meta.dir, "../../docker");

  const stream = await docker.buildImage(
    {
      context: dockerfilePath,
      src: ["Dockerfile", "entrypoint.sh"],
    },
    { t: IMAGE_NAME }
  );

  await new Promise<void>((resolve, reject) => {
    docker.modem.followProgress(stream, (err) => {
      if (err) reject(err);
      else resolve();
    });
  });
}

export async function prewarmContainer(): Promise<void> {
  if (!(await isDockerAvailable())) return;

  // Build image if needed
  if (!(await isImageBuilt())) {
    await buildImage();
  }

  // Remove any existing prewarm container
  try {
    const existing = docker.getContainer(PREWARM_NAME);
    await existing.remove({ force: true });
  } catch {}

  // Get user's tmux.conf
  const tmuxConfPath = join(homedir(), ".tmux.conf");
  const binds: string[] = [];

  try {
    await Bun.file(tmuxConfPath).text();
    binds.push(`${tmuxConfPath}:/tmp/user.tmux.conf:ro`);
  } catch {}

  // Start prewarm container
  const container = await docker.createContainer({
    Image: IMAGE_NAME,
    name: PREWARM_NAME,
    Tty: true,
    OpenStdin: true,
    HostConfig: { Binds: binds },
    Entrypoint: ["/bin/bash"],
    Cmd: [
      "-c",
      "cp /tmp/user.tmux.conf ~/.tmux.conf 2>/dev/null; tail -f /dev/null",
    ],
  });

  await container.start();
}

export async function cleanupPrewarm(): Promise<void> {
  try {
    const container = docker.getContainer(PREWARM_NAME);
    await container.remove({ force: true });
  } catch {}
}

export interface KeybindToTry {
  keybind: string;
  command: string;
  description: string;
}

export interface LaunchOptions {
  keybinds?: KeybindToTry[];
  description?: string;
}

export async function launchSandbox(options: LaunchOptions): Promise<{ success: boolean; terminal?: string }> {
  // WIP: Terminal auto-detection is work in progress
  // For now, default to kitty
  const terminal: TerminalType = "kitty";

  if (!(await hasTerminal("kitty"))) {
    return { success: false };
  }

  // Build the sandbox script
  const tmuxConfPath = join(homedir(), ".tmux.conf");
  let mounts = "";
  let setupCmd = "";

  try {
    await Bun.file(tmuxConfPath).text();
    mounts += `-v "${tmuxConfPath}:/tmp/user.tmux.conf:ro" `;
    setupCmd += "cp /tmp/user.tmux.conf ~/.tmux.conf && ";
  } catch {}

  // Create test bindings if provided
  if (options.keybinds && options.keybinds.length > 0) {
    // Characters that need quoting in tmux keybinds
    const specialChars = /[{}\[\];"'\\#]/;

    // Generate proper bind commands for each keybind
    const bindLines = options.keybinds.map(kb => {
      const isNoPrefix = kb.keybind.startsWith("M-") || kb.keybind.startsWith("C-");
      // Quote keybind if it contains special characters
      const quotedKey = specialChars.test(kb.keybind) ? `"${kb.keybind}"` : kb.keybind;
      return isNoPrefix
        ? `bind -n ${quotedKey} ${kb.command}`
        : `bind ${quotedKey} ${kb.command}`;
    });

    // Add newlines: one at start (in case user config doesn't end with newline) and one at end
    const content = "\n" + bindLines.join("\n") + "\n";

    const testFile = join(tmpdir(), "moobler-test.conf");
    await writeFile(testFile, content);

    // Also write to a debug file for inspection
    const debugFile = join(tmpdir(), "moobler-debug.conf");
    await writeFile(debugFile, `# Generated by moobler at ${new Date().toISOString()}\n${content}`);

    mounts += `-v "${testFile}:/tmp/test.conf:ro" `;
    setupCmd +=
      'echo "" >> ~/.tmux.conf && echo "# === NEW KEYBINDS ===" >> ~/.tmux.conf && cat /tmp/test.conf >> ~/.tmux.conf && ';
  }

  // Create challenge info
  let challengeDisplay = "";
  if (options.keybinds && options.keybinds.length > 0) {
    const keybindList = options.keybinds
      .map(kb => `  ${kb.keybind}: ${kb.description}`)
      .join("\\n");
    challengeDisplay = `
echo "=== PRACTICE ==="
echo "Group: ${options.description || "Keybinds"}"
echo ""
echo -e "${keybindList}"
echo "================"
echo ""
`;
  }

  const script = `#!/bin/bash
${challengeDisplay}

docker rm -f ${CONTAINER_NAME} 2>/dev/null

echo "Starting sandbox..."

docker run -it --rm --name ${CONTAINER_NAME} \\
    -e TERM=xterm-256color \\
    ${mounts}\\
    --entrypoint /bin/bash \\
    ${IMAGE_NAME} \\
    -c '${setupCmd}tmux new-session -s sandbox'

echo ""
echo "Sandbox exited. Press Enter to close..."
read
`;

  const scriptFile = join(tmpdir(), "moobler-sandbox.sh");
  await writeFile(scriptFile, script, { mode: 0o755 });

  // WIP: Other terminals (ghostty, gnome-terminal, iterm2) support coming soon
  // For now, just launch in kitty
  Bun.spawn(["kitty", "--start-as=fullscreen", "--title", "moobler sandbox", "bash", scriptFile], {
    stdin: "inherit",
    stdout: "inherit",
    stderr: "inherit",
  });

  return { success: true, terminal };
}

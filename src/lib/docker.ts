import Docker from "dockerode";
import { homedir } from "os";
import { join } from "path";
import { tmpdir } from "os";
import { writeFile, unlink } from "fs/promises";

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

export interface LaunchOptions {
  keybind?: string;
  command?: string;
  description?: string;
}

export async function launchSandbox(options: LaunchOptions): Promise<boolean> {
  // Check for kitty terminal
  const proc = Bun.spawn(["which", "kitty"]);
  await proc.exited;
  const hasKitty = proc.exitCode === 0;

  if (!hasKitty) {
    return false;
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

  // Create test binding if provided
  if (options.keybind && options.command) {
    const testBindings =
      options.keybind.startsWith("M-") || options.keybind.startsWith("C-")
        ? `bind -n ${options.keybind} ${options.command}`
        : `bind ${options.keybind} ${options.command}`;

    const testFile = join(tmpdir(), "moobler-test.conf");
    await writeFile(testFile, testBindings);
    mounts += `-v "${testFile}:/tmp/test.conf:ro" `;
    setupCmd +=
      'echo "" >> ~/.tmux.conf && echo "# === NEW KEYBIND ===" >> ~/.tmux.conf && cat /tmp/test.conf >> ~/.tmux.conf && ';
  }

  // Create challenge info
  let challengeDisplay = "";
  if (options.keybind) {
    challengeDisplay = `
echo "=== PRACTICE ==="
echo "Keybind: ${options.keybind}"
echo "Command: ${options.command || ""}"
echo "Description: ${options.description || ""}"
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

  // Launch in kitty
  Bun.spawn(["kitty", "--start-as=fullscreen", "--title", "moobler sandbox", "bash", scriptFile], {
    stdin: "inherit",
    stdout: "inherit",
    stderr: "inherit",
  });

  return true;
}

export interface ScrapedKeybind {
  keybind: string;
  command: string;
  raw: string;
  source: string;
}

const POPULAR_REPOS = [
  "gpakosz/.tmux",
  "tmux-plugins/tmux-sensible",
  "samoshkin/tmux-config",
  "tony/tmux-config",
];

async function fetchTmuxConfig(repo: string): Promise<string | null> {
  const paths = [".tmux.conf", "tmux.conf", ".tmux/.tmux.conf"];
  const branches = ["master", "main"];

  for (const branch of branches) {
    for (const path of paths) {
      try {
        const url = `https://raw.githubusercontent.com/${repo}/${branch}/${path}`;
        const response = await fetch(url);
        if (response.ok) {
          return await response.text();
        }
      } catch {
        continue;
      }
    }
  }
  return null;
}

function parseKeybinds(config: string, source: string): ScrapedKeybind[] {
  const keybinds: ScrapedKeybind[] = [];
  const lines = config.split("\n");

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    const match = trimmed.match(/^(?:bind-key|bind)\s+(.+)$/);
    if (!match) continue;

    let args = match[1];
    let prefix = "";

    if (args.startsWith("-n ")) {
      prefix = "-n ";
      args = args.slice(3);
    }

    if (args.startsWith("-T ")) {
      args = args.replace(/^-T\s+\S+\s+/, "");
    }

    const parts = args.split(/\s+/);
    if (parts.length < 2) continue;

    const key = parts[0];
    const command = parts.slice(1).join(" ");

    keybinds.push({
      keybind: prefix + key,
      command,
      raw: trimmed,
      source,
    });
  }

  return keybinds;
}

export async function scrapeGitHubConfigs(): Promise<ScrapedKeybind[]> {
  const allKeybinds: ScrapedKeybind[] = [];

  const results = await Promise.allSettled(
    POPULAR_REPOS.map(async (repo) => {
      const config = await fetchTmuxConfig(repo);
      if (config) {
        return parseKeybinds(config, repo);
      }
      return [];
    })
  );

  for (const result of results) {
    if (result.status === "fulfilled") {
      allKeybinds.push(...result.value);
    }
  }

  return allKeybinds;
}

"""GitHub scraper for finding popular tmux configurations."""

import re
from typing import Optional

import httpx
from pydantic import BaseModel, Field


class GitHubRepo(BaseModel):
    """A GitHub repository with tmux configuration."""

    name: str
    full_name: str
    description: Optional[str]
    stars: int
    url: str
    raw_config_url: Optional[str] = None


class ScrapedKeybind(BaseModel):
    """A keybinding scraped from GitHub."""

    source_repo: str
    keybind: str
    command: str
    raw_line: str
    context: Optional[str] = None  # Surrounding comments if any


# Well-known tmux dotfile repositories
POPULAR_REPOS = [
    "gpakosz/.tmux",
    "tmux-plugins/tmux-sensible",
    "samoshkin/tmux-config",
    "tony/tmux-config",
    "rothgar/awesome-tmux",
]


async def fetch_repo_info(client: httpx.AsyncClient, repo: str) -> Optional[GitHubRepo]:
    """Fetch repository information from GitHub API."""
    try:
        response = await client.get(
            f"https://api.github.com/repos/{repo}",
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        if response.status_code != 200:
            return None

        data = response.json()
        return GitHubRepo(
            name=data["name"],
            full_name=data["full_name"],
            description=data.get("description"),
            stars=data["stargazers_count"],
            url=data["html_url"],
        )
    except Exception:
        return None


async def fetch_tmux_config(client: httpx.AsyncClient, repo: str) -> Optional[str]:
    """Fetch tmux.conf content from a repository."""
    # Common locations for tmux config
    paths = [
        ".tmux.conf",
        "tmux.conf",
        ".tmux/.tmux.conf",
        "tmux/.tmux.conf",
    ]

    for path in paths:
        try:
            url = f"https://raw.githubusercontent.com/{repo}/master/{path}"
            response = await client.get(url)
            if response.status_code == 200:
                return response.text

            # Try main branch
            url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
            response = await client.get(url)
            if response.status_code == 200:
                return response.text
        except Exception:
            continue

    return None


def parse_keybinds_from_config(config: str, source_repo: str) -> list[ScrapedKeybind]:
    """Parse keybindings from a tmux config string."""
    keybinds = []
    lines = config.splitlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Match bind/bind-key commands
        match = re.match(r"^(?:bind-key|bind)\s+(.+)$", line)
        if not match:
            continue

        args = match.group(1)

        # Extract key and command
        # Handle -n flag (root binding)
        is_root = False
        if args.startswith("-n "):
            is_root = True
            args = args[3:]

        # Handle -T flag
        if args.startswith("-T "):
            # Skip for now, more complex parsing needed
            args = re.sub(r"^-T\s+\S+\s+", "", args)

        # Split into key and command
        parts = args.split(None, 1)
        if len(parts) < 2:
            continue

        key, command = parts

        # Get context from surrounding comments
        context = None
        if i > 0 and lines[i - 1].strip().startswith("#"):
            context = lines[i - 1].strip().lstrip("#").strip()

        keybinds.append(
            ScrapedKeybind(
                source_repo=source_repo,
                keybind=f"{'-n ' if is_root else ''}{key}",
                command=command,
                raw_line=line,
                context=context,
            )
        )

    return keybinds


async def scrape_github_dotfiles(
    repos: Optional[list[str]] = None,
    timeout: float = 30.0,
) -> list[ScrapedKeybind]:
    """Scrape keybindings from popular GitHub dotfile repositories.

    Args:
        repos: List of repos to scrape (default: POPULAR_REPOS)
        timeout: HTTP timeout in seconds

    Returns:
        List of scraped keybindings
    """
    if repos is None:
        repos = POPULAR_REPOS

    all_keybinds: list[ScrapedKeybind] = []

    async with httpx.AsyncClient(timeout=timeout) as client:
        for repo in repos:
            config = await fetch_tmux_config(client, repo)
            if config:
                keybinds = parse_keybinds_from_config(config, repo)
                all_keybinds.extend(keybinds)

    return all_keybinds


async def search_github_for_tmux_configs(
    query: str = "tmux.conf",
    min_stars: int = 100,
    limit: int = 10,
) -> list[GitHubRepo]:
    """Search GitHub for repositories with tmux configurations.

    Args:
        query: Search query
        min_stars: Minimum stars for results
        limit: Maximum number of results

    Returns:
        List of matching repositories
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": f"{query} stars:>{min_stars}",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": limit,
                },
                headers={"Accept": "application/vnd.github.v3+json"},
            )

            if response.status_code != 200:
                return []

            data = response.json()
            repos = []
            for item in data.get("items", []):
                repos.append(
                    GitHubRepo(
                        name=item["name"],
                        full_name=item["full_name"],
                        description=item.get("description"),
                        stars=item["stargazers_count"],
                        url=item["html_url"],
                    )
                )
            return repos
        except Exception:
            return []

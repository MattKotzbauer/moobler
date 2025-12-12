"""Smart AI-powered keybinding suggester that uses Claude + GitHub data."""

import os
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from pydantic import BaseModel

from ..discovery.github_scraper import scrape_github_dotfiles, ScrapedKeybind


class KeybindGroup(BaseModel):
    """A group of related keybindings to try together."""

    name: str  # e.g., "Pane Resize Controls"
    description: str  # What this group does
    keybinds: list[dict]  # [{keybind, command, description}, ...]
    reasoning: str  # Why these are grouped together


class SmartSuggester:
    """AI-powered suggester that analyzes config + GitHub data to make smart suggestions."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    def _read_user_config(self) -> str:
        """Read user's tmux.conf."""
        tmux_conf = Path.home() / ".tmux.conf"
        if tmux_conf.exists():
            return tmux_conf.read_text()
        return ""

    async def _fetch_github_configs(self) -> list[ScrapedKeybind]:
        """Fetch keybindings from popular GitHub configs."""
        try:
            return await scrape_github_dotfiles()
        except Exception:
            return []

    def _format_github_keybinds(self, keybinds: list[ScrapedKeybind]) -> str:
        """Format GitHub keybinds for Claude."""
        if not keybinds:
            return "No GitHub configs available."

        # Group by repo and limit
        by_repo = {}
        for kb in keybinds:
            if kb.source_repo not in by_repo:
                by_repo[kb.source_repo] = []
            if len(by_repo[kb.source_repo]) < 15:  # Limit per repo
                by_repo[kb.source_repo].append(kb)

        lines = []
        for repo, kbs in by_repo.items():
            lines.append(f"\n## From {repo}:")
            for kb in kbs:
                context = f" ({kb.context})" if kb.context else ""
                lines.append(f"  {kb.raw_line}{context}")

        return "\n".join(lines)

    async def get_smart_suggestions(
        self,
        category: Optional[str] = None,
    ) -> list[KeybindGroup]:
        """Get AI-powered suggestions grouped by related functionality.

        Args:
            category: Optional category to focus on (navigation, panes, etc.)

        Returns:
            List of KeybindGroup objects with related keybinds grouped together
        """
        # 1. Read user's config
        user_config = self._read_user_config()

        # 2. Fetch GitHub configs
        github_keybinds = await self._fetch_github_configs()
        github_formatted = self._format_github_keybinds(github_keybinds)

        # 3. Build prompt for Claude
        category_focus = f"\nFocus specifically on {category} keybindings." if category else ""

        system_prompt = """You are a tmux expert helping users discover new keybindings.

Your job is to:
1. Analyze the user's current tmux config to understand their style
2. Look at popular keybindings from GitHub configs
3. Suggest NEW keybindings that:
   - Match the user's style (if they use vim keys, suggest vim-style bindings)
   - Don't conflict with their existing bindings
   - Are genuinely useful
   - Are grouped logically (e.g., all resize bindings together)

IMPORTANT CONSTRAINTS:
- NEVER suggest C-c, C-d, C-z, C-s, C-q - these conflict with terminal control signals
- NEVER suggest C-l (clears screen) or C-a (often used as tmux prefix or readline)
- Prefer Alt/Meta bindings (M-x) for no-prefix shortcuts as they rarely conflict
- If suggesting prefix bindings, use memorable letters that aren't already common defaults

IMPORTANT: Group related keybindings together. For example:
- If suggesting resize bindings, include all 4 directions (up/down/left/right)
- If suggesting navigation, include related navigation bindings
- Each group should be something the user can practice together in one session

Respond in JSON format with this structure:
{
  "groups": [
    {
      "name": "Group Name",
      "description": "What this group of keybinds does",
      "keybinds": [
        {"keybind": "M-H", "command": "resize-pane -L 5", "description": "Resize pane left"},
        {"keybind": "M-J", "command": "resize-pane -D 5", "description": "Resize pane down"}
      ],
      "reasoning": "Why these bindings work well together and match user's style"
    }
  ]
}

Return 2-4 groups of suggestions."""

        user_prompt = f"""Here is the user's current tmux configuration:

```
{user_config if user_config else "No existing tmux.conf found - user is starting fresh"}
```

Here are popular keybindings from well-known GitHub tmux configs:

{github_formatted}
{category_focus}

Based on the user's style and these popular configs, suggest grouped keybindings.
Remember to return valid JSON."""

        # 4. Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        response_text = response.content[0].text

        # 5. Parse response
        import json
        import re

        # Extract JSON from response
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
        if json_match:
            response_text = json_match.group(1)

        try:
            data = json.loads(response_text)
            groups = []
            for g in data.get("groups", []):
                groups.append(KeybindGroup(
                    name=g.get("name", "Suggestions"),
                    description=g.get("description", ""),
                    keybinds=g.get("keybinds", []),
                    reasoning=g.get("reasoning", ""),
                ))
            return groups
        except json.JSONDecodeError:
            # Return raw as single group
            return [KeybindGroup(
                name="AI Suggestions",
                description="Suggestions from Claude",
                keybinds=[],
                reasoning=response_text,
            )]

    def generate_config_addition(
        self,
        group: KeybindGroup,
    ) -> str:
        """Generate tmux config lines for a group of keybinds.

        Args:
            group: The keybind group to generate config for

        Returns:
            Formatted tmux config lines ready to append
        """
        lines = [f"\n# {group.name}"]
        lines.append(f"# {group.description}")

        for kb in group.keybinds:
            keybind = kb.get("keybind", "")
            command = kb.get("command", "")
            desc = kb.get("description", "")

            if not keybind or not command:
                continue

            # Add comment for the keybind
            if desc:
                lines.append(f"# {desc}")

            # Determine if root binding (M- prefix means no tmux prefix needed)
            if keybind.startswith("M-") or keybind.startswith("C-") and not "prefix" in keybind.lower():
                lines.append(f"bind -n {keybind} {command}")
            else:
                lines.append(f"bind {keybind} {command}")

        return "\n".join(lines)

    async def add_group_to_config(
        self,
        group: KeybindGroup,
        backup: bool = True,
    ) -> tuple[bool, str]:
        """Add a group of keybindings to the user's tmux.conf.

        Args:
            group: The keybind group to add
            backup: Whether to backup config first

        Returns:
            (success, message) tuple
        """
        from ..config.merger import ConfigMerger

        merger = ConfigMerger()

        # Backup first
        if backup:
            try:
                backup_path = merger.backup_config()
            except FileNotFoundError:
                pass  # No existing config to backup

        # Generate config lines
        config_addition = self.generate_config_addition(group)

        # Append to config
        config_path = Path.home() / ".tmux.conf"

        try:
            existing = config_path.read_text() if config_path.exists() else ""
            config_path.write_text(existing + config_addition + "\n")

            return True, f"Added {len(group.keybinds)} keybindings to ~/.tmux.conf"
        except Exception as e:
            return False, f"Error adding to config: {e}"

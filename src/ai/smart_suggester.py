"""Smart AI-powered keybinding suggester that uses Claude + GitHub data."""

import os
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from pydantic import BaseModel

from ..discovery.github_scraper import scrape_github_dotfiles, ScrapedKeybind


class UserStyleAnalysis(BaseModel):
    """Analysis of user's keybinding style preferences."""

    prefix_preference: str  # "no-prefix (Alt/Meta)" | "prefix-based" | "mixed"
    modifier_preference: str  # "Alt/Meta" | "Ctrl" | "mixed"
    navigation_style: str  # "vim" | "arrows" | "other"
    keys_in_use: list[str]  # List of keys already bound


class KeybindGroup(BaseModel):
    """A group of related keybindings to try together."""

    name: str  # e.g., "Pane Resize Controls"
    description: str  # What this group does
    keybinds: list[dict]  # [{keybind, command, description}, ...]
    reasoning: str  # Why these are grouped together


class SuggestionResult(BaseModel):
    """Result from AI suggestion including style analysis."""

    style_analysis: Optional[UserStyleAnalysis] = None
    groups: list[KeybindGroup]


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
    ) -> SuggestionResult:
        """Get AI-powered suggestions grouped by related functionality.

        Args:
            category: Optional category to focus on (navigation, panes, etc.)

        Returns:
            SuggestionResult with style analysis and grouped keybinds
        """
        # 1. Read user's config
        user_config = self._read_user_config()

        # 2. Fetch GitHub configs
        github_keybinds = await self._fetch_github_configs()
        github_formatted = self._format_github_keybinds(github_keybinds)

        # 3. Build prompt for Claude
        category_focus = f"\nFocus specifically on {category} keybindings." if category else ""

        system_prompt = """You are a tmux expert helping users discover new keybindings.

STEP 1 - ANALYZE USER'S STYLE PATTERNS (do this carefully before suggesting anything):

Look at their config and determine:
1. **Prefix vs No-Prefix preference**:
   - Count bindings using `bind -n` (no prefix, direct shortcuts) vs `bind` (requires prefix)
   - If they predominantly use `bind -n M-...` (Alt+key), they prefer PREFIX-FREE bindings
   - If they mostly use `bind X ...` (prefix then key), they prefer PREFIX bindings
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

Return 2-4 groups of suggestions that MATCH the user's established patterns."""

        user_prompt = f"""Here is the user's current tmux configuration:

```
{user_config if user_config else "No existing tmux.conf found - user is starting fresh"}
```

Here are popular keybindings from well-known GitHub tmux configs (use these as inspiration, but ADAPT them to match the user's style):

{github_formatted}
{category_focus}

IMPORTANT: First analyze the user's config to identify their patterns:
- Do they use `bind -n` (no prefix) or `bind` (with prefix)?
- What modifiers do they prefer (M- for Alt, C- for Ctrl)?
- What keys are already taken?

Then suggest keybindings that use the SAME style. If they use Alt+key bindings everywhere,
suggest more Alt+key bindings - NOT prefix bindings.

Return valid JSON with user_style_analysis and groups."""

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

            # Parse style analysis if present
            style_analysis = None
            if "user_style_analysis" in data:
                sa = data["user_style_analysis"]
                style_analysis = UserStyleAnalysis(
                    prefix_preference=sa.get("prefix_preference", "unknown"),
                    modifier_preference=sa.get("modifier_preference", "unknown"),
                    navigation_style=sa.get("navigation_style", "unknown"),
                    keys_in_use=sa.get("keys_in_use", []),
                )

            # Parse groups
            groups = []
            for g in data.get("groups", []):
                groups.append(KeybindGroup(
                    name=g.get("name", "Suggestions"),
                    description=g.get("description", ""),
                    keybinds=g.get("keybinds", []),
                    reasoning=g.get("reasoning", ""),
                ))

            return SuggestionResult(style_analysis=style_analysis, groups=groups)
        except json.JSONDecodeError:
            # Return raw as single group
            return SuggestionResult(
                style_analysis=None,
                groups=[KeybindGroup(
                    name="AI Suggestions",
                    description="Suggestions from Claude",
                    keybinds=[],
                    reasoning=response_text,
                )]
            )

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

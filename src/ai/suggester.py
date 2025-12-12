"""AI-powered keybinding suggester."""

from typing import Optional

from ..config.models import TmuxConfig, KeyModifier, BindingMode
from ..discovery.curated import get_curated_tips, CuratedTip
from .client import ClaudeClient


class KeybindSuggester:
    """Suggests keybindings based on user's config and style."""

    def __init__(self, client: Optional[ClaudeClient] = None):
        """Initialize the suggester.

        Args:
            client: Optional ClaudeClient for AI-powered suggestions.
                   Falls back to rule-based suggestions if not provided.
        """
        self.client = client

    def _get_complementary_keys(self, config: TmuxConfig) -> list[CuratedTip]:
        """Get complementary keybindings based on existing config style."""
        suggestions = []
        style = config.style

        # If user uses M-hjkl for navigation, suggest M-HJKL for resize
        if style.navigation_pattern == "M-hjkl":
            if not config.has_binding("M-H", BindingMode.ROOT):
                tips = get_curated_tips(category="resize", no_prefix_only=True)
                suggestions.extend([t for t in tips if "M-H" in t.keybind])

        # If user uses vim keys with prefix, suggest vim copy mode
        if style.uses_vim_keys:
            vim_copy = get_curated_tips(category="copy", vim_only=True)
            # Check if they already have vim copy mode
            has_vim_copy = any(
                "copy-mode-vi" in kb.command.lower() for kb in config.keybindings
            )
            if not has_vim_copy:
                suggestions.extend(vim_copy)

        # If user doesn't have quick window switching
        has_window_switch = any(
            "select-window" in kb.command and kb.mode == BindingMode.ROOT
            for kb in config.keybindings
        )
        if not has_window_switch:
            window_tips = get_curated_tips(category="navigation")
            suggestions.extend([t for t in window_tips if "M-1" in t.keybind])

        return suggestions

    def _get_missing_essentials(self, config: TmuxConfig) -> list[CuratedTip]:
        """Find essential keybindings the user is missing."""
        suggestions = []
        essentials = [
            ("reload-config", "source-file"),
            ("pane-zoom", "resize-pane -Z"),
            ("session-picker", "choose-tree"),
        ]

        for tip_id, cmd_pattern in essentials:
            has_binding = any(cmd_pattern in kb.command for kb in config.keybindings)
            if not has_binding:
                from ..discovery.curated import get_tip_by_id

                if tip := get_tip_by_id(tip_id):
                    suggestions.append(tip)

        return suggestions

    def get_suggestions(
        self,
        config: TmuxConfig,
        category: Optional[str] = None,
        limit: int = 10,
    ) -> list[CuratedTip]:
        """Get keybinding suggestions for a user's config.

        Args:
            config: Parsed tmux configuration
            category: Optional category to filter suggestions
            limit: Maximum number of suggestions

        Returns:
            List of suggested keybindings
        """
        suggestions = []

        # Get complementary keybindings based on style
        suggestions.extend(self._get_complementary_keys(config))

        # Get missing essentials
        suggestions.extend(self._get_missing_essentials(config))

        # Add category-specific tips if requested
        if category:
            category_tips = get_curated_tips(category=category)
            # Filter out ones that conflict with existing bindings
            for tip in category_tips:
                if tip not in suggestions:
                    suggestions.append(tip)

        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for tip in suggestions:
            if tip.id not in seen:
                seen.add(tip.id)
                unique_suggestions.append(tip)

        return unique_suggestions[:limit]

    async def get_ai_suggestions(
        self,
        config: TmuxConfig,
        category: Optional[str] = None,
    ) -> list[dict]:
        """Get AI-powered keybinding suggestions.

        Args:
            config: Parsed tmux configuration
            category: Optional category to focus on

        Returns:
            List of AI-generated suggestions
        """
        if not self.client:
            raise ValueError("ClaudeClient required for AI suggestions")

        user_style = {
            "prefix": config.style.prefix_key,
            "uses_vim_keys": config.style.uses_vim_keys,
            "uses_arrow_keys": config.style.uses_arrow_keys,
            "prefers_meta": config.style.prefers_meta,
            "navigation_pattern": config.style.navigation_pattern,
        }

        existing_bindings = [kb.key_combo for kb in config.keybindings]

        return await self.client.suggest_keybinds(
            user_style=user_style,
            existing_bindings=existing_bindings,
            category=category,
        )

    def rank_suggestions(
        self,
        suggestions: list[CuratedTip],
        config: TmuxConfig,
    ) -> list[CuratedTip]:
        """Rank suggestions by relevance to user's style.

        Args:
            suggestions: List of suggestions to rank
            config: User's tmux configuration

        Returns:
            Sorted list with most relevant first
        """

        def score(tip: CuratedTip) -> int:
            s = 0
            # Bonus for matching vim style
            if config.style.uses_vim_keys and tip.vim_style:
                s += 10
            # Bonus for matching prefix preference
            if config.style.prefers_meta and not tip.requires_prefix:
                s += 5
            # Bonus for beginner tips if user has few bindings
            if len(config.keybindings) < 20 and tip.difficulty == "beginner":
                s += 3
            # Penalty for advanced tips if user seems like beginner
            if len(config.keybindings) < 10 and tip.difficulty == "advanced":
                s -= 5
            return s

        return sorted(suggestions, key=score, reverse=True)

"""Screen for discovering new keybindings."""

import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static, LoadingIndicator, ListView, ListItem

from ..widgets.keybind_card import KeybindCard
from ...config import parse_tmux_config
from ...ai.suggester import KeybindSuggester
from ...discovery.curated import get_curated_tips


class DiscoverScreen(Screen):
    """Discover and browse new keybinding suggestions."""

    CSS = """
    #discover-layout {
        height: 1fr;
    }

    #categories {
        width: 25;
        height: 100%;
        border: solid $primary;
        padding: 1;
    }

    #category-list {
        height: 1fr;
    }

    #category-list > ListItem {
        padding: 0 1;
    }

    #category-list > ListItem:hover {
        background: $surface-lighten-1;
    }

    #category-list > ListItem.-selected {
        background: $primary;
    }

    #suggestions {
        width: 1fr;
        height: 100%;
        padding: 0 1;
    }

    #suggestion-list {
        height: 1fr;
    }

    #discover-actions {
        height: auto;
        padding: 1 0;
    }

    #discover-actions Button {
        margin-right: 1;
    }

    .section-header {
        text-style: bold;
        margin-bottom: 1;
    }

    KeybindCard {
        margin: 1 0;
    }

    KeybindCard.-selected {
        border: solid $success;
        background: $surface-lighten-1;
    }
    """

    BINDINGS = [
        # j/k navigate suggestions, h/l switch panels
        Binding("j", "next_suggestion", "Next", show=False),
        Binding("k", "prev_suggestion", "Prev", show=False),
        Binding("h", "focus_categories", "Categories", show=False),
        Binding("l", "focus_suggestions", "Suggestions", show=False),
        Binding("enter", "select_item", "Select", show=False),
        Binding("o", "select_item", "Open", show=False),
        Binding("t", "try_selected", "Try It", show=False),
        Binding("a", "add_selected", "Add", show=False),
        Binding("ctrl+d", "scroll_down", "Scroll Down", show=False),
        Binding("ctrl+u", "scroll_up", "Scroll Up", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._selected_card_index = 0
        self._in_suggestions = False
        self._current_category = "navigation"

    def action_next_suggestion(self) -> None:
        """Move to next suggestion card or category item."""
        if self._in_suggestions:
            cards = list(self.query(KeybindCard))
            if cards:
                # Deselect current
                if 0 <= self._selected_card_index < len(cards):
                    cards[self._selected_card_index].remove_class("-selected")
                # Move to next
                self._selected_card_index = min(self._selected_card_index + 1, len(cards) - 1)
                cards[self._selected_card_index].add_class("-selected")
                cards[self._selected_card_index].scroll_visible()
        else:
            # In categories list
            try:
                cat_list = self.query_one("#category-list", ListView)
                cat_list.action_cursor_down()
            except Exception:
                pass

    def action_prev_suggestion(self) -> None:
        """Move to previous suggestion card or category item."""
        if self._in_suggestions:
            cards = list(self.query(KeybindCard))
            if cards:
                # Deselect current
                if 0 <= self._selected_card_index < len(cards):
                    cards[self._selected_card_index].remove_class("-selected")
                # Move to prev
                self._selected_card_index = max(self._selected_card_index - 1, 0)
                cards[self._selected_card_index].add_class("-selected")
                cards[self._selected_card_index].scroll_visible()
        else:
            # In categories list
            try:
                cat_list = self.query_one("#category-list", ListView)
                cat_list.action_cursor_up()
            except Exception:
                pass

    def action_focus_categories(self) -> None:
        """Switch focus to categories panel (h key)."""
        self._in_suggestions = False
        # Deselect any selected card
        for card in self.query(KeybindCard):
            card.remove_class("-selected")
        try:
            self.query_one("#category-list", ListView).focus()
        except Exception:
            pass

    def action_focus_suggestions(self) -> None:
        """Switch focus to suggestions panel (l key)."""
        self._in_suggestions = True
        cards = list(self.query(KeybindCard))
        if cards:
            self._selected_card_index = 0
            cards[0].add_class("-selected")
            cards[0].scroll_visible()

    def action_select_item(self) -> None:
        """Select current item (enter/o)."""
        if self._in_suggestions:
            # Try the selected keybind
            self._try_selected_keybind()
        else:
            # Select category in list (triggers on_list_view_selected)
            try:
                cat_list = self.query_one("#category-list", ListView)
                cat_list.action_select_cursor()
            except Exception:
                pass

    def action_try_selected(self) -> None:
        """Try the selected keybind in sandbox."""
        self._try_selected_keybind()

    def action_add_selected(self) -> None:
        """Add the selected keybind to config."""
        cards = list(self.query(KeybindCard))
        if cards and 0 <= self._selected_card_index < len(cards):
            card = cards[self._selected_card_index]
            self.app.notify(
                f"Adding '{card.keybind}' to your config...",
                title="Add to Config",
            )
            # TODO: Actually add to config using ConfigMerger

    def _try_selected_keybind(self) -> None:
        """Launch sandbox with the selected keybind."""
        cards = list(self.query(KeybindCard))
        if cards and 0 <= self._selected_card_index < len(cards):
            card = cards[self._selected_card_index]
            # Store the keybind to try in the app
            self.app._keybind_to_try = {
                "keybind": card.keybind,
                "command": card.command,
                "description": card.description,
            }
            self.app.switch_screen("sandbox")

    def action_scroll_down(self) -> None:
        """Scroll down half page (vim Ctrl+d)."""
        container = self.query_one("#suggestion-list", ScrollableContainer)
        container.scroll_down(animate=False)
        container.scroll_down(animate=False)
        container.scroll_down(animate=False)

    def action_scroll_up(self) -> None:
        """Scroll up half page (vim Ctrl+u)."""
        container = self.query_one("#suggestion-list", ScrollableContainer)
        container.scroll_up(animate=False)
        container.scroll_up(animate=False)
        container.scroll_up(animate=False)

    def compose(self) -> ComposeResult:
        """Compose the discover screen."""
        with Container(id="main-content"):
            yield Static("Discover New Keybinds", classes="title")
            yield Static(
                "AI-powered suggestions based on your config",
                classes="subtitle",
            )

            with Horizontal(id="discover-layout"):
                with Vertical(id="categories"):
                    yield Label("Categories", classes="section-header")
                    yield ListView(
                        ListItem(Label("Navigation"), id="cat-nav"),
                        ListItem(Label("Window Management"), id="cat-window"),
                        ListItem(Label("Pane Management"), id="cat-pane"),
                        ListItem(Label("Copy Mode"), id="cat-copy"),
                        ListItem(Label("Session Management"), id="cat-session"),
                        ListItem(Label("Productivity"), id="cat-productivity"),
                        id="category-list",
                    )

                with Vertical(id="suggestions"):
                    yield Label("Suggestions", classes="section-header")
                    yield LoadingIndicator(id="loading")
                    yield ScrollableContainer(id="suggestion-list")

            with Horizontal(id="discover-actions"):
                yield Button("Back", id="btn-back", variant="default")
                yield Button("Search Online", id="btn-search", variant="primary")
                yield Button("Refresh Suggestions", id="btn-refresh", variant="success")

    def on_mount(self) -> None:
        """Load initial suggestions."""
        self.query_one("#loading").display = False
        self._user_config = None
        self._suggester = KeybindSuggester()
        self._load_user_config()
        self._load_suggestions("navigation")

    def _load_user_config(self) -> None:
        """Load user's tmux config for personalized suggestions."""
        tmux_conf = Path.home() / ".tmux.conf"
        if tmux_conf.exists():
            self._user_config = parse_tmux_config(str(tmux_conf))

    def _load_suggestions(self, category: str) -> None:
        """Load suggestions for a category based on user's config."""
        container = self.query_one("#suggestion-list", ScrollableContainer)
        container.remove_children()
        self._selected_card_index = 0

        # Map UI categories to curated tip categories
        category_map = {
            "navigation": "navigation",
            "window": "navigation",  # Window nav is in navigation
            "pane": "panes",
            "copy": "copy",
            "session": "session",
            "productivity": "productivity",
        }
        tip_category = category_map.get(category, "navigation")

        suggestions = []

        # Get curated tips for this category
        curated = get_curated_tips(category=tip_category)

        # If we have user config, filter and personalize suggestions
        if self._user_config:
            style = self._user_config.style

            for tip in curated:
                # Skip tips the user already has
                existing_keys = [kb.key_combo for kb in self._user_config.keybindings]
                if any(tip.keybind.replace("prefix + ", "") in k for k in existing_keys):
                    continue

                # Prioritize vim-style tips if user uses vim keys
                if style.uses_vim_keys and tip.vim_style:
                    suggestions.insert(0, {
                        "keybind": tip.keybind,
                        "description": f"[Matches your vim style] {tip.description}",
                        "command": tip.command,
                    })
                # Prioritize no-prefix tips if user prefers Meta bindings
                elif style.prefers_meta and not tip.requires_prefix:
                    suggestions.insert(0, {
                        "keybind": tip.keybind,
                        "description": f"[Matches your Alt/Meta style] {tip.description}",
                        "command": tip.command,
                    })
                else:
                    suggestions.append({
                        "keybind": tip.keybind,
                        "description": tip.description,
                        "command": tip.command,
                    })

            # Add style-specific suggestions based on user's patterns
            if category == "navigation" and style.navigation_pattern == "M-hjkl":
                # User has M-hjkl for navigation, suggest M-HJKL for resize
                resize_suggestions = [
                    {"keybind": "M-H", "description": "Resize pane left (complements your M-h)", "command": "resize-pane -L 5"},
                    {"keybind": "M-J", "description": "Resize pane down (complements your M-j)", "command": "resize-pane -D 5"},
                    {"keybind": "M-K", "description": "Resize pane up (complements your M-k)", "command": "resize-pane -U 5"},
                    {"keybind": "M-L", "description": "Resize pane right (complements your M-l)", "command": "resize-pane -R 5"},
                ]
                # Only add if user doesn't have these
                for s in resize_suggestions:
                    if not self._user_config.has_binding(s["keybind"], mode=self._user_config.keybindings[0].mode if self._user_config.keybindings else None):
                        suggestions.insert(0, s)
        else:
            # No user config, just show all curated tips
            for tip in curated:
                suggestions.append({
                    "keybind": tip.keybind,
                    "description": tip.description,
                    "command": tip.command,
                })

        # If no suggestions, show fallback
        if not suggestions:
            suggestions = self._get_fallback_suggestions(category)

        # Create cards
        for suggestion in suggestions[:10]:  # Limit to 10
            card = KeybindCard(
                keybind=suggestion["keybind"],
                description=suggestion["description"],
                command=suggestion["command"],
                category=category,
            )
            container.mount(card)

    def _get_fallback_suggestions(self, category: str) -> list[dict]:
        """Fallback suggestions if nothing else matches."""
        fallbacks = {
            "navigation": [
                {"keybind": "M-h/j/k/l", "description": "Vim-style pane navigation without prefix", "command": "bind -n M-h select-pane -L"},
            ],
            "window": [
                {"keybind": "M-1..9", "description": "Quick switch to window N", "command": "bind -n M-1 select-window -t 1"},
            ],
            "pane": [
                {"keybind": "prefix + |", "description": "Split horizontally (visual)", "command": "split-window -h"},
                {"keybind": "prefix + -", "description": "Split vertically (visual)", "command": "split-window -v"},
            ],
            "copy": [
                {"keybind": "prefix + [", "description": "Enter copy mode", "command": "copy-mode"},
            ],
            "session": [
                {"keybind": "prefix + s", "description": "Session picker", "command": "choose-tree -s"},
            ],
            "productivity": [
                {"keybind": "prefix + r", "description": "Reload config", "command": "source-file ~/.tmux.conf"},
            ],
        }
        return fallbacks.get(category, fallbacks["navigation"])

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle category selection."""
        item_id = event.item.id or ""
        category_map = {
            "cat-nav": "navigation",
            "cat-window": "window",
            "cat-pane": "pane",
            "cat-copy": "copy",
            "cat-session": "session",
            "cat-productivity": "productivity",
        }
        category = category_map.get(item_id, "navigation")
        self._current_category = category
        self._load_suggestions(category)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.switch_screen("home")
        elif event.button.id == "btn-search":
            self.run_worker(self._fetch_ai_suggestions())
        elif event.button.id == "btn-refresh":
            self._load_suggestions(self._current_category)
            self.app.notify(
                "Suggestions refreshed",
                title="Refresh",
            )

    async def _fetch_ai_suggestions(self) -> None:
        """Fetch AI-powered suggestions from Claude."""
        loading = self.query_one("#loading", LoadingIndicator)
        loading.display = True

        try:
            from ...ai.client import ClaudeClient
            client = ClaudeClient()

            # Get user's style and existing bindings
            style = {}
            existing = []
            if self._user_config:
                style = self._user_config.style.model_dump()
                existing = [kb.key_combo for kb in self._user_config.keybindings]

            # Get current category
            category = getattr(self, "_current_category", "navigation")

            self.app.notify("Asking Claude for suggestions...", title="AI Search")

            # Call Claude API
            suggestions = await client.suggest_keybinds(
                user_style=style,
                existing_bindings=existing,
                category=category,
            )

            if not suggestions:
                self.app.notify("No suggestions returned", title="AI Search")
                return

            # Add AI suggestions to the display
            container = self.query_one("#suggestion-list", ScrollableContainer)

            for s in suggestions:
                keybind = s.get("keybind", "")
                description = s.get("description", "")
                command = s.get("command", "")
                reasoning = s.get("reasoning", "")

                # Skip if missing required fields
                if not keybind or not command:
                    continue

                # Add reasoning to description if available
                full_desc = f"[AI] {description}"
                if reasoning:
                    full_desc += f" ({reasoning})"

                card = KeybindCard(
                    keybind=keybind,
                    description=full_desc,
                    command=command,
                    category=category,
                )
                container.mount(card)

            self.app.notify(f"Added {len(suggestions)} AI suggestions!", title="AI Search")

        except ValueError as e:
            # API key not set
            self.app.notify(
                "Set ANTHROPIC_API_KEY to use AI suggestions",
                title="API Key Required",
            )
        except Exception as e:
            self.app.notify(
                f"Error: {str(e)[:50]}",
                title="AI Search Failed",
            )
        finally:
            loading.display = False

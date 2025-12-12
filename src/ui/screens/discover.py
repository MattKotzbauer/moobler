"""Screen for discovering new keybindings."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static, LoadingIndicator, ListView, ListItem

from ..widgets.keybind_card import KeybindCard


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
    """

    BINDINGS = [
        # Vim bindings for this screen
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("ctrl+d", "scroll_down", "Scroll Down", show=False),
        Binding("ctrl+u", "scroll_up", "Scroll Up", show=False),
    ]

    def action_cursor_down(self) -> None:
        """Move cursor down in focused list."""
        focused = self.focused
        if isinstance(focused, ListView):
            focused.action_cursor_down()
        else:
            self.focus_next()

    def action_cursor_up(self) -> None:
        """Move cursor up in focused list."""
        focused = self.focused
        if isinstance(focused, ListView):
            focused.action_cursor_up()
        else:
            self.focus_previous()

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
        self._load_suggestions("navigation")

    def _load_suggestions(self, category: str) -> None:
        """Load suggestions for a category."""
        container = self.query_one("#suggestion-list", ScrollableContainer)
        container.remove_children()

        # Sample suggestions (will be replaced with AI-generated ones)
        suggestions = self._get_sample_suggestions(category)

        for suggestion in suggestions:
            card = KeybindCard(
                keybind=suggestion["keybind"],
                description=suggestion["description"],
                command=suggestion["command"],
                category=category,
            )
            container.mount(card)

    def _get_sample_suggestions(self, category: str) -> list[dict]:
        """Get sample suggestions for demo purposes."""
        samples = {
            "navigation": [
                {
                    "keybind": "M-H",
                    "description": "Resize pane left (pairs with M-h for select)",
                    "command": "resize-pane -L 5",
                },
                {
                    "keybind": "M-J",
                    "description": "Resize pane down",
                    "command": "resize-pane -D 5",
                },
                {
                    "keybind": "M-K",
                    "description": "Resize pane up",
                    "command": "resize-pane -U 5",
                },
                {
                    "keybind": "M-L",
                    "description": "Resize pane right",
                    "command": "resize-pane -R 5",
                },
            ],
            "window": [
                {
                    "keybind": "M-1..9",
                    "description": "Quick switch to window N without prefix",
                    "command": "select-window -t :=N",
                },
                {
                    "keybind": "M-Tab",
                    "description": "Cycle through windows",
                    "command": "next-window",
                },
            ],
            "pane": [
                {
                    "keybind": "prefix + |",
                    "description": "Split horizontally (visual mnemonic)",
                    "command": "split-window -h",
                },
                {
                    "keybind": "prefix + -",
                    "description": "Split vertically (visual mnemonic)",
                    "command": "split-window -v",
                },
                {
                    "keybind": "prefix + z",
                    "description": "Zoom/unzoom current pane",
                    "command": "resize-pane -Z",
                },
            ],
            "copy": [
                {
                    "keybind": "prefix + [",
                    "description": "Enter copy mode",
                    "command": "copy-mode",
                },
                {
                    "keybind": "v (in copy)",
                    "description": "Begin selection (vim-style)",
                    "command": "begin-selection",
                },
                {
                    "keybind": "y (in copy)",
                    "description": "Copy selection (vim-style)",
                    "command": "copy-selection-and-cancel",
                },
            ],
            "session": [
                {
                    "keybind": "prefix + $",
                    "description": "Rename current session",
                    "command": "command-prompt -I '#S' 'rename-session %%'",
                },
                {
                    "keybind": "prefix + s",
                    "description": "Interactive session picker",
                    "command": "choose-tree -s",
                },
            ],
            "productivity": [
                {
                    "keybind": "prefix + r",
                    "description": "Reload tmux config",
                    "command": "source-file ~/.tmux.conf",
                },
                {
                    "keybind": "prefix + ?",
                    "description": "List all keybindings",
                    "command": "list-keys",
                },
            ],
        }

        return samples.get(category, samples["navigation"])

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
        self._load_suggestions(category)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.switch_screen("home")
        elif event.button.id == "btn-search":
            self.app.notify(
                "AI web search coming soon!",
                title="Search",
            )
        elif event.button.id == "btn-refresh":
            self.app.notify(
                "Refreshing suggestions...",
                title="Refresh",
            )

"""Home screen with welcome and quick actions."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ...config import parse_tmux_config


class HomeScreen(Screen):
    """Welcome screen with overview and quick actions."""

    CSS = """
    #status-section {
        height: auto;
        margin: 1 0;
        padding: 1;
        background: $surface-darken-1;
        border: solid $primary;
    }

    #actions {
        height: auto;
        margin: 1 0;
    }

    #actions Button {
        width: 100%;
        margin: 1 0;
    }

    #actions Button:focus {
        background: $success;
    }
    """

    BINDINGS = [
        Binding("j", "focus_next", "Down", show=False),
        Binding("k", "focus_previous", "Up", show=False),
        Binding("enter", "press_button", "Select", show=False),
        Binding("o", "press_button", "Open", show=False),
        Binding("l", "press_button", "Open", show=False),
    ]

    def action_press_button(self) -> None:
        """Press the focused button."""
        focused = self.focused
        if isinstance(focused, Button):
            focused.press()

    def compose(self) -> ComposeResult:
        """Compose the home screen."""
        with Container(id="main-content"):
            yield Static("tmux-learn", classes="title")
            yield Static(
                "Learn new tmux controls with AI-powered suggestions",
                classes="subtitle",
            )

            with Vertical(id="status-section"):
                yield Label("", id="config-status")

            with Vertical(id="actions"):
                yield Button("View My Config", id="btn-config", variant="primary")
                yield Button("Discover New Keybinds", id="btn-discover", variant="success")
                yield Button("Try in Sandbox", id="btn-sandbox", variant="warning")
                yield Button("My Progress", id="btn-progress", variant="default")

            yield Static(
                "Press ? for keyboard shortcuts",
                classes="hint",
            )

    def on_mount(self) -> None:
        """Check for existing tmux config on mount."""
        self._update_config_status()

    def _update_config_status(self) -> None:
        """Update the config status display."""
        tmux_conf = Path.home() / ".tmux.conf"
        status_label = self.query_one("#config-status", Label)

        if tmux_conf.exists():
            config = parse_tmux_config(str(tmux_conf))
            binding_count = len(config.keybindings)
            style_info = []
            if config.style.uses_vim_keys:
                style_info.append("vim-style")
            if config.style.uses_arrow_keys:
                style_info.append("arrow keys")
            if config.style.prefers_meta:
                style_info.append("Alt/Meta bindings")
            style_str = ", ".join(style_info) if style_info else "standard"

            status_label.update(
                f"Found ~/.tmux.conf with {binding_count} keybindings ({style_str})"
            )
        else:
            status_label.update(
                "No ~/.tmux.conf found - we'll help you create one!"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-config":
            self.app.switch_screen("config")
        elif button_id == "btn-discover":
            self.app.switch_screen("discover")
        elif button_id == "btn-sandbox":
            self.app.switch_screen("sandbox")
        elif button_id == "btn-progress":
            self.app.notify("Progress tracking coming soon!", title="Progress")

"""Screen for viewing and understanding current tmux config."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Horizontal
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label, Static, TabbedContent, TabPane

from ...config import parse_tmux_config, BindingMode


class ConfigViewScreen(Screen):
    """Display and analyze the user's current tmux configuration."""

    def compose(self) -> ComposeResult:
        """Compose the config view screen."""
        with Container(id="main-content"):
            yield Static("Your Tmux Configuration", classes="title")

            with TabbedContent():
                with TabPane("Keybindings", id="tab-bindings"):
                    yield DataTable(id="bindings-table")

                with TabPane("Style Analysis", id="tab-style"):
                    yield ScrollableContainer(
                        Static("", id="style-analysis"),
                        id="style-container",
                    )

                with TabPane("Raw Options", id="tab-options"):
                    yield ScrollableContainer(
                        Static("", id="raw-options"),
                        id="options-container",
                    )

            with Horizontal(id="config-actions"):
                yield Button("Back to Home", id="btn-back", variant="default")
                yield Button("Refresh", id="btn-refresh", variant="primary")

    def on_mount(self) -> None:
        """Load config data on mount."""
        self._load_config()

    def _load_config(self) -> None:
        """Load and display the tmux configuration."""
        tmux_conf = Path.home() / ".tmux.conf"

        if not tmux_conf.exists():
            self.query_one("#style-analysis", Static).update(
                "No ~/.tmux.conf found.\n\n"
                "Would you like to generate a sensible default config?"
            )
            return

        config = parse_tmux_config(str(tmux_conf))

        # Populate bindings table
        table = self.query_one("#bindings-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Key", "Mode", "Command", "Type")

        for kb in config.keybindings:
            kb_type = "nav" if kb.is_navigation else "resize" if kb.is_resize else "split" if kb.is_split else "-"
            table.add_row(
                kb.key_combo,
                kb.mode.value,
                kb.command[:50] + "..." if len(kb.command) > 50 else kb.command,
                kb_type,
            )

        # Style analysis
        style = config.style
        style_text = f"""Configuration Analysis
{'=' * 40}

Prefix Key: {style.prefix_key}

Navigation Style:
  - Uses vim keys (h/j/k/l): {'Yes' if style.uses_vim_keys else 'No'}
  - Uses arrow keys: {'Yes' if style.uses_arrow_keys else 'No'}
  - Navigation pattern: {style.navigation_pattern or 'Not detected'}

Modifier Preferences:
  - Prefers Meta/Alt: {'Yes' if style.prefers_meta else 'No'}
  - Prefers Ctrl: {'Yes' if style.prefers_ctrl else 'No'}

Statistics:
  - Total keybindings: {len(config.keybindings)}
  - Prefix bindings: {len(config.get_bindings_for_mode(BindingMode.PREFIX))}
  - Root bindings (no prefix): {len(config.get_bindings_for_mode(BindingMode.ROOT))}
  - Copy-mode bindings: {len(config.get_bindings_for_mode(BindingMode.COPY_MODE)) + len(config.get_bindings_for_mode(BindingMode.COPY_MODE_VI))}
"""
        self.query_one("#style-analysis", Static).update(style_text)

        # Raw options
        if config.raw_options:
            options_text = "Set Options\n" + "=" * 40 + "\n\n"
            for key, value in config.raw_options.items():
                options_text += f"{key}: {value}\n"
        else:
            options_text = "No set options found in config."

        self.query_one("#raw-options", Static).update(options_text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.switch_screen("home")
        elif event.button.id == "btn-refresh":
            self._load_config()
            self.app.notify("Config reloaded", title="Refresh")

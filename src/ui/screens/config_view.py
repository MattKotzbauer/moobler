"""Screen for viewing and understanding current tmux config."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, ScrollableContainer, Horizontal
from textual.screen import Screen
from textual.widgets import Button, DataTable, Label, Static, TabbedContent, TabPane

from ...config import parse_tmux_config, BindingMode


class ConfigViewScreen(Screen):
    """Display and analyze the user's current tmux configuration."""

    CSS = """
    #bindings-table {
        height: 1fr;
    }

    #style-container, #options-container {
        height: 1fr;
    }

    #config-actions {
        height: auto;
        padding: 1 0;
    }

    #config-actions Button {
        margin-right: 1;
    }

    DataTable > .datatable--cursor {
        background: $primary;
    }
    """

    BINDINGS = [
        # Vim navigation for table
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("h", "prev_tab", "Prev Tab", show=False),
        Binding("l", "next_tab", "Next Tab", show=False),
        Binding("ctrl+d", "page_down", "Page Down", show=False),
        Binding("ctrl+u", "page_up", "Page Up", show=False),
        Binding("g", "go_top", "Top", show=False),
        Binding("G", "go_bottom", "Bottom", show=False),
    ]

    def action_cursor_down(self) -> None:
        """Move cursor down in table."""
        try:
            table = self.query_one("#bindings-table", DataTable)
            if self.focused == table:
                table.action_cursor_down()
            else:
                self.focus_next()
        except Exception:
            self.focus_next()

    def action_cursor_up(self) -> None:
        """Move cursor up in table."""
        try:
            table = self.query_one("#bindings-table", DataTable)
            if self.focused == table:
                table.action_cursor_up()
            else:
                self.focus_previous()
        except Exception:
            self.focus_previous()

    def action_prev_tab(self) -> None:
        """Go to previous tab."""
        try:
            tabs = self.query_one(TabbedContent)
            tabs.action_previous_tab()
        except Exception:
            pass

    def action_next_tab(self) -> None:
        """Go to next tab."""
        try:
            tabs = self.query_one(TabbedContent)
            tabs.action_next_tab()
        except Exception:
            pass

    def action_page_down(self) -> None:
        """Page down in table."""
        try:
            table = self.query_one("#bindings-table", DataTable)
            for _ in range(10):
                table.action_cursor_down()
        except Exception:
            pass

    def action_page_up(self) -> None:
        """Page up in table."""
        try:
            table = self.query_one("#bindings-table", DataTable)
            for _ in range(10):
                table.action_cursor_up()
        except Exception:
            pass

    def action_go_top(self) -> None:
        """Go to top of table."""
        try:
            table = self.query_one("#bindings-table", DataTable)
            table.cursor_coordinate = (0, 0)
        except Exception:
            pass

    def action_go_bottom(self) -> None:
        """Go to bottom of table."""
        try:
            table = self.query_one("#bindings-table", DataTable)
            table.cursor_coordinate = (table.row_count - 1, 0)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """Compose the config view screen."""
        with Container(id="main-content"):
            yield Static("Your Tmux Configuration", classes="title")

            with TabbedContent():
                with TabPane("Keybindings", id="tab-bindings"):
                    yield DataTable(id="bindings-table")

                with TabPane("Style Analysis", id="tab-style"):
                    yield ScrollableContainer(
                        Static("", id="style-analysis", markup=False),
                        id="style-container",
                    )

                with TabPane("Raw Options", id="tab-options"):
                    yield ScrollableContainer(
                        Static("", id="raw-options", markup=False),
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

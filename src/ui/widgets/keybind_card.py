"""Widget for displaying a keybinding suggestion."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Static


class KeybindCard(Widget, can_focus=True):
    """A card displaying a keybinding suggestion."""

    DEFAULT_CSS = """
    KeybindCard {
        height: auto;
        margin: 1 0;
        padding: 1 2;
        border: solid $primary;
        background: $surface-darken-1;
    }

    KeybindCard:focus {
        border: solid $success;
        background: $surface-lighten-1;
    }

    KeybindCard:hover {
        background: $surface-lighten-1;
    }

    KeybindCard .keybind-key {
        color: $success;
        text-style: bold;
        width: 15;
    }

    KeybindCard .keybind-desc {
        color: $text;
        width: 1fr;
    }

    KeybindCard .keybind-command {
        color: $warning;
        text-style: italic;
    }

    KeybindCard .card-actions {
        margin-top: 1;
    }

    KeybindCard Button {
        margin-right: 1;
    }

    KeybindCard Button.-active {
        background: $success;
        border: solid $success-lighten-1;
    }
    """

    BINDINGS = [
        Binding("h", "prev_action", "Prev", show=False),
        Binding("l", "next_action", "Next", show=False),
        Binding("enter", "activate_action", "Select", show=False),
        Binding("o", "activate_action", "Select", show=False),
        Binding("t", "try_keybind", "Try", show=False),
        Binding("a", "add_keybind", "Add", show=False),
        Binding("d", "show_details", "Details", show=False),
    ]

    class TryKeybind(Message):
        """Message emitted when user wants to try a keybind."""

        def __init__(self, keybind: str, command: str, description: str) -> None:
            self.keybind = keybind
            self.command = command
            self.description = description
            super().__init__()

    class AddKeybind(Message):
        """Message emitted when user wants to add a keybind."""

        def __init__(self, keybind: str, command: str) -> None:
            self.keybind = keybind
            self.command = command
            super().__init__()

    def __init__(
        self,
        keybind: str,
        description: str,
        command: str,
        category: str = "",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.keybind = keybind
        self.description = description
        self.command = command
        self.category = category
        self._selected_action = 0  # 0=Try, 1=Add, 2=Details

    def compose(self) -> ComposeResult:
        """Compose the card."""
        yield Label(self.keybind, classes="keybind-key")
        yield Static(self.description, classes="keybind-desc")
        yield Static(f"Command: {self.command}", classes="keybind-command")

        with Horizontal(classes="card-actions"):
            yield Button("Try It (t)", id="btn-try", variant="primary")
            yield Button("Add (a)", id="btn-add", variant="success")
            yield Button("Details (d)", id="btn-details", variant="default")

    def on_mount(self) -> None:
        """Highlight default action on mount."""
        self._update_action_highlight()

    def _update_action_highlight(self) -> None:
        """Update which button is highlighted."""
        buttons = list(self.query(Button))
        for i, btn in enumerate(buttons):
            if i == self._selected_action:
                btn.add_class("-active")
            else:
                btn.remove_class("-active")

    def action_prev_action(self) -> None:
        """Move to previous action (h key)."""
        self._selected_action = max(0, self._selected_action - 1)
        self._update_action_highlight()

    def action_next_action(self) -> None:
        """Move to next action (l key)."""
        self._selected_action = min(2, self._selected_action + 1)
        self._update_action_highlight()

    def action_activate_action(self) -> None:
        """Activate the selected action (enter/o)."""
        if self._selected_action == 0:
            self.action_try_keybind()
        elif self._selected_action == 1:
            self.action_add_keybind()
        else:
            self.action_show_details()

    def action_try_keybind(self) -> None:
        """Try this keybind in sandbox."""
        self.post_message(self.TryKeybind(self.keybind, self.command, self.description))
        # Store in app and switch to sandbox
        self.app._keybind_to_try = {
            "keybind": self.keybind,
            "command": self.command,
            "description": self.description,
        }
        self.app.switch_screen("sandbox")

    def action_add_keybind(self) -> None:
        """Add this keybind to config."""
        self.post_message(self.AddKeybind(self.keybind, self.command))
        self.app.notify(f"Adding '{self.keybind}' to config...", title="Add")
        # TODO: Actually add using ConfigMerger

    def action_show_details(self) -> None:
        """Show details about this keybind."""
        self.app.notify(
            f"{self.keybind}: {self.description}\n\nCommand: {self.command}",
            title="Keybind Details",
            timeout=8,
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses within the card."""
        event.stop()

        if event.button.id == "btn-try":
            self.action_try_keybind()
        elif event.button.id == "btn-add":
            self.action_add_keybind()
        elif event.button.id == "btn-details":
            self.action_show_details()

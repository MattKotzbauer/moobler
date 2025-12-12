"""Widget for displaying a keybinding suggestion."""

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Label, Static


class KeybindCard(Widget):
    """A card displaying a keybinding suggestion."""

    DEFAULT_CSS = """
    KeybindCard {
        height: auto;
        margin: 1 0;
        padding: 1 2;
        border: solid $primary;
        background: $surface-darken-1;
    }

    KeybindCard:hover {
        background: $surface-lighten-1;
        border: solid $success;
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
    """

    class TryKeybind(Message):
        """Message emitted when user wants to try a keybind."""

        def __init__(self, keybind: str, command: str) -> None:
            self.keybind = keybind
            self.command = command
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

    def compose(self) -> ComposeResult:
        """Compose the card."""
        yield Label(self.keybind, classes="keybind-key")
        yield Static(self.description, classes="keybind-desc")
        yield Static(f"Command: {self.command}", classes="keybind-command")

        with Horizontal(classes="card-actions"):
            yield Button("Try It", id="btn-try", variant="primary")
            yield Button("Add to Config", id="btn-add", variant="success")
            yield Button("Details", id="btn-details", variant="default")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses within the card."""
        event.stop()

        if event.button.id == "btn-try":
            self.post_message(self.TryKeybind(self.keybind, self.command))
            self.app.notify(f"Try '{self.keybind}' in the sandbox!", title="Try It")
        elif event.button.id == "btn-add":
            self.post_message(self.AddKeybind(self.keybind, self.command))
            self.app.notify(f"Adding '{self.keybind}' to config...", title="Add")
        elif event.button.id == "btn-details":
            self.app.notify(
                f"{self.keybind}: {self.description}\n\nCommand: {self.command}",
                title="Keybind Details",
            )

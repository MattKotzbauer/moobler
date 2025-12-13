"""
Multi-step sequence controller for keybind practice.
"""

import sys
from dataclasses import dataclass
from typing import List

from PySide6.QtCore import QTimer

from .keybind_parser import parse_keybind, get_expected_key
from .window import OverlayWindow


@dataclass
class KeybindStep:
    """A single step in the practice sequence."""
    keybind: str        # tmux notation, e.g., "M-H"
    description: str    # e.g., "Resize pane left"


class SequenceController:
    """
    Controls the flow through a sequence of keybinds.
    Uses Qt's native key handling instead of pynput.
    """

    def __init__(self, steps: List[KeybindStep], window: OverlayWindow, debug: bool = False):
        self.steps = steps
        self.window = window
        self.current_index = 0
        self.completed = False
        self.escaped = False
        self.debug = debug

        self.expected_modifiers: set[str] = set()
        self.expected_key: str = ""

        # Connect to window's key signal
        self.window.signals.key_pressed.connect(self._on_key)

    def _debug(self, msg: str):
        if self.debug:
            print(f"[SEQ] {msg}", file=sys.stderr)

    def start(self):
        """Start the sequence practice."""
        if not self.steps:
            self.completed = True
            self.window.close_overlay()
            return

        self._show_current()

    def stop(self):
        """Stop the sequence practice."""
        pass  # No cleanup needed for Qt-based handling

    def _show_current(self):
        """Display the current keybind."""
        step = self.steps[self.current_index]

        # Get display text
        display_keybind = parse_keybind(step.keybind)

        # Update window
        self.window.update_keybind(
            display_keybind,
            step.description,
            self.current_index + 1,
            len(self.steps),
        )

        # Set expected key
        self.expected_modifiers, self.expected_key = get_expected_key(step.keybind)
        self._debug(f"Expecting: mods={self.expected_modifiers}, key='{self.expected_key}'")

    def _on_key(self, key: str, modifiers_list: list):
        """Handle key press from Qt."""
        modifiers = set(modifiers_list)  # Convert list back to set
        self._debug(f"Key received: '{key}', mods={modifiers}")

        # Check for escape
        if key == "escape":
            self._debug("ESCAPE - exiting")
            self._on_escape()
            return

        # Check if matches expected
        self._debug(f"Comparing: got=({modifiers}, '{key}') vs expected=({self.expected_modifiers}, '{self.expected_key}')")

        if key == self.expected_key and modifiers == self.expected_modifiers:
            self._debug("CORRECT!")
            self._on_correct()
        else:
            self._debug("Wrong key")
            self._on_wrong()

    def _on_correct(self):
        """Handle correct key press."""
        # Flash success
        self.window.flash_success()

        # Advance to next step after brief delay
        self.current_index += 1

        if self.current_index >= len(self.steps):
            # Completed all steps - close after showing green flash
            self.completed = True
            QTimer.singleShot(300, self.window.close_overlay)
        else:
            # Show next keybind after brief delay
            QTimer.singleShot(300, self._show_current)

    def _on_escape(self):
        """Handle escape key press."""
        self.escaped = True
        self.window.close_overlay()

    def _on_wrong(self):
        """Handle wrong key press."""
        self.window.flash_wrong()

        # Reset to normal after brief flash
        QTimer.singleShot(150, self._show_current)

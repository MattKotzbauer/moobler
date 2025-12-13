"""
Global keyboard capture using pynput.
"""

from pynput import keyboard
from typing import Callable, Optional
import threading
import sys


class KeyboardListener:
    """
    Captures global keyboard input and checks for expected keybinds.
    """

    def __init__(
        self,
        on_correct: Callable[[], None],
        on_escape: Callable[[], None],
        on_wrong: Optional[Callable[[], None]] = None,
        debug: bool = False,
    ):
        self.on_correct = on_correct
        self.on_escape = on_escape
        self.on_wrong = on_wrong
        self.debug = debug

        self.expected_modifiers: set[str] = set()
        self.expected_key: str = ""

        self._listener: Optional[keyboard.Listener] = None
        self._pressed_modifiers: set[str] = set()
        self._lock = threading.Lock()

    def _debug(self, msg: str):
        if self.debug:
            print(f"[KB] {msg}", file=sys.stderr)

    def set_expected(self, modifiers: set[str], key: str):
        """Set the expected keybind to match."""
        with self._lock:
            self.expected_modifiers = modifiers
            self.expected_key = key
            self._debug(f"Expecting: mods={modifiers}, key={key}")

    def start(self):
        """Start capturing keyboard input."""
        self._debug("Starting keyboard listener")
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
            suppress=True,  # Suppress keys from reaching other apps
        )
        self._listener.start()

    def stop(self):
        """Stop capturing keyboard input."""
        self._debug("Stopping keyboard listener")
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _get_key_name(self, key) -> str:
        """Get normalized key name from pynput key."""
        try:
            # Regular character key
            if hasattr(key, "char") and key.char:
                return key.char.lower()
        except AttributeError:
            pass

        # Special keys
        key_map = {
            keyboard.Key.space: "space",
            keyboard.Key.enter: "enter",
            keyboard.Key.tab: "tab",
            keyboard.Key.backspace: "backspace",
            keyboard.Key.escape: "escape",
            keyboard.Key.up: "up",
            keyboard.Key.down: "down",
            keyboard.Key.left: "left",
            keyboard.Key.right: "right",
        }

        return key_map.get(key, str(key).replace("Key.", "").lower())

    def _on_press(self, key):
        """Handle key press events."""
        self._debug(f"Key pressed: {key} (type: {type(key).__name__})")

        # Check for escape FIRST (always allow exit)
        if key == keyboard.Key.escape:
            self._debug("ESCAPE detected - exiting")
            self.on_escape()
            return

        # Track modifier state
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            self._pressed_modifiers.add("alt")
            self._debug(f"Alt pressed, modifiers: {self._pressed_modifiers}")
            return
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._pressed_modifiers.add("ctrl")
            self._debug(f"Ctrl pressed, modifiers: {self._pressed_modifiers}")
            return
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._pressed_modifiers.add("shift")
            self._debug(f"Shift pressed, modifiers: {self._pressed_modifiers}")
            return

        # Get the pressed key name
        key_name = self._get_key_name(key)
        self._debug(f"Key name: {key_name}, current modifiers: {self._pressed_modifiers}")

        with self._lock:
            # Check if this matches the expected keybind
            modifiers_match = self._pressed_modifiers == self.expected_modifiers
            key_matches = key_name == self.expected_key

            self._debug(f"Match check: mods_match={modifiers_match}, key_match={key_matches}")
            self._debug(f"  pressed_mods={self._pressed_modifiers}, expected_mods={self.expected_modifiers}")
            self._debug(f"  pressed_key={key_name}, expected_key={self.expected_key}")

            if modifiers_match and key_matches:
                self._debug("CORRECT!")
                self.on_correct()
            elif self.on_wrong:
                self._debug("Wrong key")
                self.on_wrong()

    def _on_release(self, key):
        """Handle key release events."""
        # Track modifier state
        if key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr):
            self._pressed_modifiers.discard("alt")
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self._pressed_modifiers.discard("ctrl")
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            self._pressed_modifiers.discard("shift")

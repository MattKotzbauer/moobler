"""Challenge generation using AI."""

from typing import Optional

from .client import ClaudeClient


class ChallengeGenerator:
    """Generates interactive learning challenges."""

    def __init__(self, client: Optional[ClaudeClient] = None):
        """Initialize the generator.

        Args:
            client: ClaudeClient for AI generation. If not provided,
                   uses pre-built challenge templates.
        """
        self.client = client

    async def generate_for_keybind(
        self,
        keybind: str,
        command: str,
        difficulty: str = "beginner",
    ) -> dict:
        """Generate a challenge for learning a specific keybind.

        Args:
            keybind: The keybind to learn (e.g., "M-h")
            command: The tmux command (e.g., "select-pane -L")
            difficulty: beginner, intermediate, or advanced

        Returns:
            Challenge definition dict
        """
        if self.client:
            return await self.client.generate_challenge(keybind, command, difficulty)

        # Fallback to template-based generation
        return self._generate_from_template(keybind, command, difficulty)

    def _generate_from_template(
        self,
        keybind: str,
        command: str,
        difficulty: str,
    ) -> dict:
        """Generate a challenge using pre-built templates."""
        # Detect command type and use appropriate template
        if "select-pane" in command:
            return self._pane_navigation_challenge(keybind, command)
        elif "resize-pane" in command:
            return self._pane_resize_challenge(keybind, command)
        elif "split-window" in command:
            return self._split_challenge(keybind, command)
        elif "select-window" in command:
            return self._window_navigation_challenge(keybind, command)
        elif "copy" in command.lower():
            return self._copy_mode_challenge(keybind, command)
        else:
            return self._generic_challenge(keybind, command)

    def _pane_navigation_challenge(self, keybind: str, command: str) -> dict:
        """Challenge for pane navigation keybinds."""
        direction = "left" if "-L" in command else \
                   "down" if "-D" in command else \
                   "up" if "-U" in command else \
                   "right" if "-R" in command else "another pane"

        return {
            "objective": f"Navigate to the pane on the {direction}",
            "setup": {
                "panes": 4,
                "layout": "tiled",
                "start_pane": 0,
                "target_pane": {"left": 2, "right": 1, "up": 2, "down": 3}.get(direction, 1),
            },
            "expected_keys": [keybind],
            "success_criteria": f"Active pane is now on the {direction}",
            "hint": f"Press {keybind} to move {direction}",
        }

    def _pane_resize_challenge(self, keybind: str, command: str) -> dict:
        """Challenge for pane resize keybinds."""
        direction = "left" if "-L" in command else \
                   "down" if "-D" in command else \
                   "up" if "-U" in command else \
                   "right" if "-R" in command else "unknown"

        return {
            "objective": f"Resize the current pane {direction}ward",
            "setup": {
                "panes": 2,
                "layout": "even-horizontal" if direction in ["left", "right"] else "even-vertical",
                "start_pane": 0,
            },
            "expected_keys": [keybind],
            "success_criteria": f"Pane boundary moved {direction}",
            "hint": f"Press {keybind} to resize {direction}. You may need to press multiple times.",
        }

    def _split_challenge(self, keybind: str, command: str) -> dict:
        """Challenge for split keybinds."""
        is_horizontal = "-h" in command
        direction = "horizontally (side by side)" if is_horizontal else "vertically (top/bottom)"

        return {
            "objective": f"Split the current pane {direction}",
            "setup": {
                "panes": 1,
                "layout": "single",
            },
            "expected_keys": [keybind],
            "success_criteria": f"Window now has 2 panes arranged {direction}",
            "hint": f"Press {keybind} to create a new pane",
        }

    def _window_navigation_challenge(self, keybind: str, command: str) -> dict:
        """Challenge for window navigation keybinds."""
        return {
            "objective": "Switch to a different window",
            "setup": {
                "windows": 3,
                "start_window": 1,
            },
            "expected_keys": [keybind],
            "success_criteria": "Active window changed",
            "hint": f"Press {keybind} to switch windows",
        }

    def _copy_mode_challenge(self, keybind: str, command: str) -> dict:
        """Challenge for copy mode keybinds."""
        return {
            "objective": "Enter copy mode and select some text",
            "setup": {
                "panes": 1,
                "content": "Sample text to copy:\nLine 1\nLine 2\nLine 3",
            },
            "expected_keys": ["prefix + [", keybind],
            "success_criteria": "Text was copied to tmux buffer",
            "hint": "First enter copy mode with prefix + [, then use the keybind",
        }

    def _generic_challenge(self, keybind: str, command: str) -> dict:
        """Generic challenge for unknown command types."""
        return {
            "objective": f"Execute the command: {command}",
            "setup": {"panes": 1},
            "expected_keys": [keybind],
            "success_criteria": "Command executed successfully",
            "hint": f"Press {keybind}",
        }

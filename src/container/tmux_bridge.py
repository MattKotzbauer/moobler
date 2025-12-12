"""Bridge between TUI and container tmux for challenge validation."""

import asyncio
from typing import Optional, Callable, Awaitable

from .manager import ContainerManager


class TmuxBridge:
    """Bridge for communicating with tmux in the container."""

    def __init__(self, manager: ContainerManager):
        """Initialize the bridge.

        Args:
            manager: ContainerManager instance
        """
        self.manager = manager
        self._key_handlers: list[Callable[[str], Awaitable[None]]] = []

    async def setup_challenge(self, setup: dict) -> None:
        """Set up a challenge environment in the container.

        Args:
            setup: Challenge setup configuration
        """
        if not self.manager.is_running():
            raise RuntimeError("Container not running")

        # Parse setup config
        panes = setup.get("panes", 1)
        layout = setup.get("layout", "tiled")
        windows = setup.get("windows", 1)
        content = setup.get("content")

        # Kill existing panes and create fresh layout
        await self.manager.exec_command("tmux kill-pane -a -t learn:0")

        # Create required panes
        for _ in range(panes - 1):
            await self.manager.exec_command("tmux split-window -t learn")

        # Apply layout
        if layout == "tiled":
            await self.manager.exec_command("tmux select-layout -t learn tiled")
        elif layout == "even-horizontal":
            await self.manager.exec_command("tmux select-layout -t learn even-horizontal")
        elif layout == "even-vertical":
            await self.manager.exec_command("tmux select-layout -t learn even-vertical")

        # Create additional windows if needed
        for i in range(windows - 1):
            await self.manager.exec_command(f"tmux new-window -t learn")

        # Add content if specified
        if content:
            await self.manager.exec_command(
                f"tmux send-keys -t learn:0 'echo \"{content}\"' Enter"
            )

        # Select starting pane/window
        start_pane = setup.get("start_pane", 0)
        start_window = setup.get("start_window", 0)
        await self.manager.exec_command(f"tmux select-window -t learn:{start_window}")
        await self.manager.exec_command(f"tmux select-pane -t learn:{start_pane}")

    async def get_current_state(self) -> dict:
        """Get the current tmux state.

        Returns:
            Dict with current pane, window, layout info
        """
        # Get active pane
        _, active_pane = await self.manager.exec_command(
            "tmux display-message -p '#{pane_index}'"
        )

        # Get active window
        _, active_window = await self.manager.exec_command(
            "tmux display-message -p '#{window_index}'"
        )

        # Get pane count
        _, pane_count = await self.manager.exec_command(
            "tmux list-panes -t learn | wc -l"
        )

        # Get window count
        _, window_count = await self.manager.exec_command(
            "tmux list-windows -t learn | wc -l"
        )

        # Get layout
        _, layout = await self.manager.exec_command(
            "tmux display-message -p '#{window_layout}'"
        )

        return {
            "active_pane": int(active_pane.strip()) if active_pane.strip().isdigit() else 0,
            "active_window": int(active_window.strip()) if active_window.strip().isdigit() else 0,
            "pane_count": int(pane_count.strip()) if pane_count.strip().isdigit() else 1,
            "window_count": int(window_count.strip()) if window_count.strip().isdigit() else 1,
            "layout": layout.strip(),
        }

    async def verify_challenge(
        self,
        expected: dict,
        initial_state: dict,
    ) -> tuple[bool, str]:
        """Verify if a challenge was completed successfully.

        Args:
            expected: Expected state/criteria from challenge
            initial_state: State before challenge started

        Returns:
            Tuple of (success, message)
        """
        current = await self.get_current_state()

        # Check for pane navigation
        if "target_pane" in expected:
            if current["active_pane"] == expected["target_pane"]:
                return True, "Correct! You navigated to the right pane."
            return False, f"Not quite - you're in pane {current['active_pane']}, expected {expected['target_pane']}"

        # Check for window change
        if "target_window" in expected:
            if current["active_window"] == expected["target_window"]:
                return True, "Correct! You switched to the right window."
            return False, f"Not quite - you're in window {current['active_window']}"

        # Check for pane count change (splits)
        if "min_panes" in expected:
            if current["pane_count"] >= expected["min_panes"]:
                return True, "Correct! You created a new pane."
            return False, f"You need at least {expected['min_panes']} panes, currently have {current['pane_count']}"

        # Check for resize (layout changed)
        if expected.get("check_resize"):
            if current["layout"] != initial_state.get("layout"):
                return True, "Correct! You resized the pane."
            return False, "The pane layout hasn't changed yet."

        # Generic success if no specific criteria
        return True, "Challenge completed!"

    async def wait_for_key(self, timeout: float = 30.0) -> Optional[str]:
        """Wait for a key press in the container.

        Note: This is a simplified implementation. A full implementation
        would need to hook into tmux's key capture mechanism.

        Args:
            timeout: Maximum time to wait

        Returns:
            The key pressed, or None if timeout
        """
        # For now, we can't directly capture keys from the container
        # The user would interact via `docker exec -it` terminal
        # This is a placeholder for future enhancement
        await asyncio.sleep(0.1)
        return None

"""Screen for the containerized tmux sandbox."""

import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static, Log

from ...container.manager import ContainerManager
from ...config import parse_tmux_config


class SandboxScreen(Screen):
    """Interactive sandbox for trying new keybindings in a container."""

    CSS = """
    #sandbox-area {
        height: 1fr;
    }

    #container-status {
        padding: 1;
        background: $surface-darken-1;
        border: solid $warning;
        margin: 1 0;
    }

    #active-keybinds {
        padding: 1;
        background: $success-darken-2;
        border: solid $success;
        margin: 1 0;
    }

    #instructions {
        padding: 1;
        background: $primary-darken-2;
        border: solid $primary;
        margin: 1 0;
    }

    #container-log {
        height: 1fr;
        border: solid $primary;
    }

    #sandbox-actions {
        height: auto;
        padding: 1 0;
    }

    #sandbox-actions Button {
        margin-right: 1;
    }

    .section-header {
        text-style: bold;
        margin: 1 0;
    }
    """

    BINDINGS = [
        Binding("j", "focus_next", "Down", show=False),
        Binding("k", "focus_previous", "Up", show=False),
        Binding("enter", "press_button", "Select", show=False),
        Binding("o", "press_button", "Open", show=False),
        Binding("s", "start_sandbox", "Start", show=False),
        Binding("x", "stop_sandbox", "Stop", show=False),
        Binding("ctrl+d", "scroll_log_down", "Scroll Down", show=False),
        Binding("ctrl+u", "scroll_log_up", "Scroll Up", show=False),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._container_manager = ContainerManager()
        self._keybind_to_try = None

    def action_press_button(self) -> None:
        """Press the focused button."""
        focused = self.focused
        if isinstance(focused, Button):
            focused.press()

    def action_start_sandbox(self) -> None:
        """Start sandbox with 's' key."""
        self.run_worker(self._start_sandbox())

    def action_stop_sandbox(self) -> None:
        """Stop sandbox with 'x' key."""
        self.run_worker(self._stop_sandbox())

    def action_scroll_log_down(self) -> None:
        """Scroll log down."""
        try:
            log = self.query_one("#container-log", Log)
            log.scroll_down(animate=False)
            log.scroll_down(animate=False)
            log.scroll_down(animate=False)
        except Exception:
            pass

    def action_scroll_log_up(self) -> None:
        """Scroll log up."""
        try:
            log = self.query_one("#container-log", Log)
            log.scroll_up(animate=False)
            log.scroll_up(animate=False)
            log.scroll_up(animate=False)
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        """Compose the sandbox screen."""
        with Container(id="main-content"):
            yield Static("Tmux Sandbox", classes="title")
            yield Static(
                "Try new keybindings in a safe containerized environment",
                classes="subtitle",
            )

            with Vertical(id="sandbox-area"):
                yield Label("Container Status", classes="section-header")
                yield Static("Not running", id="container-status")

                yield Label("Keybind to Try", classes="section-header")
                yield Static("None selected - go to Discover (3) to pick one", id="active-keybinds", markup=False)

                yield Label("Instructions", classes="section-header")
                yield Static("Press 's' to start sandbox, then run the docker command below", id="instructions", markup=False)

                yield Label("Log", classes="section-header")
                yield Log(id="container-log", highlight=True)

            with Horizontal(id="sandbox-actions"):
                yield Button("Back", id="btn-back", variant="default")
                yield Button("Start Sandbox (s)", id="btn-start", variant="success")
                yield Button("Stop Sandbox (x)", id="btn-stop", variant="error")
                yield Button("Apply to Config", id="btn-apply", variant="warning")

    def on_mount(self) -> None:
        """Initialize sandbox state."""
        self._update_status("Ready to start")
        self._check_for_keybind()

    def on_screen_resume(self) -> None:
        """Called when screen is shown again."""
        self._check_for_keybind()

    def _check_for_keybind(self) -> None:
        """Check if there's a keybind to try from the discover screen."""
        keybind_info = getattr(self.app, "_keybind_to_try", None)
        if keybind_info:
            self._keybind_to_try = keybind_info
            keybind_text = (
                f"Keybind: {keybind_info['keybind']}\n"
                f"Command: {keybind_info['command']}\n"
                f"Description: {keybind_info['description']}"
            )
            self.query_one("#active-keybinds", Static).update(keybind_text)
            self._log(f"Ready to try: {keybind_info['keybind']} -> {keybind_info['command']}")

    def _update_status(self, status: str) -> None:
        """Update the container status display."""
        self.query_one("#container-status", Static).update(status)

    def _log(self, message: str) -> None:
        """Add a message to the container log."""
        log = self.query_one("#container-log", Log)
        log.write_line(message)

    def _generate_test_config(self) -> str:
        """Generate tmux config lines for the keybind being tested."""
        if not self._keybind_to_try:
            return ""

        kb = self._keybind_to_try
        keybind = kb["keybind"]
        command = kb["command"]

        # Determine if it's a root binding (M- prefix usually means no prefix needed)
        if keybind.startswith("M-"):
            return f"bind -n {keybind} {command}"
        else:
            return f"bind {keybind} {command}"

    async def _start_sandbox(self) -> None:
        """Start the Docker sandbox."""
        self._update_status("Starting container...")
        self._log("")
        self._log("=" * 50)
        self._log("Starting tmux sandbox...")
        self._log("=" * 50)

        # Get user's current config
        user_config = None
        tmux_conf = Path.home() / ".tmux.conf"
        if tmux_conf.exists():
            user_config = tmux_conf.read_text()
            self._log(f"Loaded your config from {tmux_conf}")

        # Generate test bindings
        test_bindings = self._generate_test_config()
        if test_bindings:
            self._log(f"Adding test binding: {test_bindings}")

        try:
            # Check if Docker is available
            try:
                self._container_manager.client.ping()
            except Exception as e:
                self._log(f"ERROR: Docker not available: {e}")
                self._log("")
                self._log("Please make sure Docker is installed and running:")
                self._log("  sudo systemctl start docker")
                self._update_status("Error: Docker not available")
                return

            # Build image if needed
            if not self._container_manager.is_image_built():
                self._log("Building sandbox image (first time only)...")
                self._log("This may take a minute...")
                try:
                    await self._container_manager.build_image()
                    self._log("Image built successfully!")
                except Exception as e:
                    self._log(f"ERROR building image: {e}")
                    self._log("")
                    self._log("You can build manually:")
                    self._log("  cd docker && docker build -t tmux-learn-sandbox .")
                    self._update_status("Error: Failed to build image")
                    return

            # Start container
            self._log("Starting container...")
            container_id = await self._container_manager.start(
                user_config=user_config,
                test_bindings=test_bindings,
            )

            self._update_status(f"Running (ID: {container_id[:12]})")
            self._log("")
            self._log("Container started successfully!")
            self._log("")
            self._log("=" * 50)
            self._log("TO CONNECT TO THE SANDBOX:")
            self._log("=" * 50)
            self._log("")
            self._log("  " + self._container_manager.get_attach_command())
            self._log("")
            if self._keybind_to_try:
                self._log(f"Try your new keybind: {self._keybind_to_try['keybind']}")
                self._log(f"It should: {self._keybind_to_try['description']}")
            self._log("")
            self._log("Changes are ephemeral - exit sandbox to discard.")
            self._log("Press 'x' or click Stop to end the sandbox.")

        except Exception as e:
            self._log(f"ERROR: {e}")
            self._update_status("Error starting container")

    async def _stop_sandbox(self) -> None:
        """Stop the Docker sandbox."""
        self._update_status("Stopping container...")
        self._log("")
        self._log("Stopping sandbox...")

        try:
            await self._container_manager.stop()
            self._log("Container stopped and removed.")
            self._update_status("Not running")
        except Exception as e:
            self._log(f"ERROR stopping: {e}")
            self._update_status("Error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.switch_screen("home")
        elif event.button.id == "btn-start":
            self.run_worker(self._start_sandbox())
        elif event.button.id == "btn-stop":
            self.run_worker(self._stop_sandbox())
        elif event.button.id == "btn-apply":
            if self._keybind_to_try:
                self.app.notify(
                    f"Adding {self._keybind_to_try['keybind']} to your config...",
                    title="Apply Changes",
                )
                # TODO: Actually apply using ConfigMerger
            else:
                self.app.notify(
                    "No keybind selected. Go to Discover (3) first.",
                    title="No Keybind",
                )

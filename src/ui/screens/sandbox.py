"""Screen for the containerized tmux sandbox."""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static, Log


class SandboxScreen(Screen):
    """Interactive sandbox for trying new keybindings in a container."""

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

                yield Label("Active Keybinds Being Tested", classes="section-header")
                yield Static("None selected", id="active-keybinds")

                yield Label("Container Output", classes="section-header")
                yield Log(id="container-log", highlight=True, markup=True)

            with Horizontal(id="sandbox-actions"):
                yield Button("Back", id="btn-back", variant="default")
                yield Button("Start Sandbox", id="btn-start", variant="success")
                yield Button("Stop Sandbox", id="btn-stop", variant="error")
                yield Button("Apply Changes", id="btn-apply", variant="warning")

    def on_mount(self) -> None:
        """Initialize sandbox state."""
        self._update_status("Ready to start")

    def _update_status(self, status: str) -> None:
        """Update the container status display."""
        self.query_one("#container-status", Static).update(status)

    def _log(self, message: str) -> None:
        """Add a message to the container log."""
        log = self.query_one("#container-log", Log)
        log.write_line(message)

    async def _start_sandbox(self) -> None:
        """Start the Docker sandbox."""
        self._update_status("Starting container...")
        self._log("Pulling tmux-sandbox image...")

        # TODO: Integrate with ContainerManager
        self._log("Creating container with your config...")
        self._log("Container started!")
        self._update_status("Running (container-id: demo)")
        self._log("")
        self._log("To connect to the sandbox, run:")
        self._log("  docker exec -it tmux-sandbox tmux attach")
        self._log("")
        self._log("Try your new keybindings! Changes are ephemeral.")

    async def _stop_sandbox(self) -> None:
        """Stop the Docker sandbox."""
        self._update_status("Stopping container...")
        self._log("Stopping container...")

        # TODO: Integrate with ContainerManager
        self._log("Container stopped and removed.")
        self._update_status("Not running")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.switch_screen("home")
        elif event.button.id == "btn-start":
            self.run_worker(self._start_sandbox())
        elif event.button.id == "btn-stop":
            self.run_worker(self._stop_sandbox())
        elif event.button.id == "btn-apply":
            self.app.notify(
                "This will merge tested keybindings into your config",
                title="Apply Changes",
            )

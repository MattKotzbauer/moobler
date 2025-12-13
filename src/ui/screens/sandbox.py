"""Screen for the containerized tmux sandbox."""

import os
import shutil
import subprocess
import tempfile
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
        self._keybind_group = None  # Group of related keybinds
        self._challenge = None

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
        """Check if there's a keybind or group to try from the discover screen."""
        # Check for group first
        keybind_group = getattr(self.app, "_keybind_group", None)
        if keybind_group:
            self._keybind_group = keybind_group
            self._keybind_to_try = None  # Using group mode

            # Display group info
            lines = [f"Group: {keybind_group.name}", f"{keybind_group.description}", ""]
            for kb in keybind_group.keybinds:
                lines.append(f"  {kb.get('keybind', '')}: {kb.get('description', '')}")

            self.query_one("#active-keybinds", Static).update("\n".join(lines))
            self._log(f"Ready to try group: {keybind_group.name}")
            self._log(f"{len(keybind_group.keybinds)} keybinds to practice together")

            # Generate challenge for the group
            self.run_worker(self._generate_challenge())
            return

        # Check for single keybind
        keybind_info = getattr(self.app, "_keybind_to_try", None)
        if keybind_info:
            self._keybind_to_try = keybind_info
            self._keybind_group = None

            keybind_text = (
                f"Keybind: {keybind_info['keybind']}\n"
                f"Command: {keybind_info['command']}\n"
                f"Description: {keybind_info['description']}"
            )
            self.query_one("#active-keybinds", Static).update(keybind_text)
            self._log(f"Ready to try: {keybind_info['keybind']} -> {keybind_info['command']}")

            # Generate a challenge for this keybind
            self.run_worker(self._generate_challenge())

    async def _generate_challenge(self) -> None:
        """Generate an AI challenge for the current keybind."""
        if not self._keybind_to_try:
            return

        try:
            from ...ai.client import ClaudeClient
            client = ClaudeClient()

            self._log("Generating practice challenge...")

            challenge = await client.generate_challenge(
                keybind=self._keybind_to_try["keybind"],
                command=self._keybind_to_try["command"],
                difficulty="beginner",
            )

            self._challenge = challenge

            # Display the challenge
            if challenge and "objective" in challenge:
                self._log("")
                self._log("=" * 50)
                self._log("CHALLENGE")
                self._log("=" * 50)
                self._log(f"Objective: {challenge.get('objective', 'Practice the keybind')}")
                if challenge.get("setup"):
                    self._log(f"Setup: {challenge.get('setup')}")
                if challenge.get("hint"):
                    self._log(f"Hint: {challenge.get('hint')}")
                self._log("=" * 50)
            else:
                self._log("Challenge ready - practice the keybind!")

        except ValueError:
            # API key not set - use simple fallback challenge
            self._challenge = {
                "objective": f"Practice using {self._keybind_to_try['keybind']}",
                "hint": f"This keybind executes: {self._keybind_to_try['command']}",
            }
            self._log("Practice the keybind in the sandbox!")
        except Exception as e:
            self._log(f"Could not generate challenge: {e}")

    def _update_status(self, status: str) -> None:
        """Update the container status display."""
        self.query_one("#container-status", Static).update(status)

    def _log(self, message: str) -> None:
        """Add a message to the container log."""
        log = self.query_one("#container-log", Log)
        log.write_line(message)

    def _generate_test_config(self) -> str:
        """Generate tmux config lines for the keybind(s) being tested."""
        lines = []

        # Handle group of keybinds
        if self._keybind_group:
            for kb in self._keybind_group.keybinds:
                keybind = kb.get("keybind", "")
                command = kb.get("command", "")
                if not keybind or not command:
                    continue

                if keybind.startswith("M-") or keybind.startswith("C-"):
                    lines.append(f"bind -n {keybind} {command}")
                else:
                    lines.append(f"bind {keybind} {command}")
            return "\n".join(lines)

        # Handle single keybind
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

    def _is_prewarm_ready(self) -> bool:
        """Check if a pre-warmed container is available and not already used."""
        # Check if app has marked prewarm as used (dirty)
        if not getattr(self.app, "_prewarm_ready", False):
            return False

        prewarm_name = getattr(self.app, "PREWARM_CONTAINER_NAME", "moobler-prewarm")
        try:
            container = self._container_manager.client.containers.get(prewarm_name)
            return container.status == "running"
        except Exception:
            return False

    def _mark_prewarm_used(self) -> None:
        """Mark pre-warm as used so we don't try to use a dirty container."""
        self.app._prewarm_ready = False

    def _build_sandbox_script(self, user_config: str | None, test_bindings: str) -> str:
        """Build a shell script that sets up and runs the sandbox."""
        # Build challenge display
        challenge_display = ""

        # Handle group of keybinds
        if self._keybind_group:
            group = self._keybind_group
            keybind_lines = ""
            for kb in group.keybinds:
                keybind_lines += f'echo "  {kb.get("keybind", "")}: {kb.get("description", "")}"\n'

            challenge_display = f'''
echo "=== PRACTICE GROUP ==="
echo "{group.name}"
echo "{group.description}"
echo ""
echo "Keybinds to try:"
{keybind_lines}
echo "======================"
echo ""
'''
        elif self._keybind_to_try:
            kb = self._keybind_to_try
            if self._challenge and "objective" in self._challenge:
                obj = self._challenge.get("objective", "").replace("'", "'\\''")
                hint = self._challenge.get("hint", "").replace("'", "'\\''")
                challenge_display = f'''
echo "=== CHALLENGE ==="
echo "Keybind: {kb["keybind"]}"
echo "Objective: {obj}"
echo "Hint: {hint}"
echo "=================="
echo ""
'''
            else:
                challenge_display = f'''
echo "=== CHALLENGE ==="
echo "Try: {kb["keybind"]}"
echo "Command: {kb["command"]}"
echo "=================="
echo ""
'''

        # Build volume mounts for config
        mounts = ""
        setup_cmd = ""

        # Mount user's tmux.conf if it exists
        tmux_conf_path = Path.home() / ".tmux.conf"
        if tmux_conf_path.exists():
            mounts += f'-v "{tmux_conf_path}:/tmp/user.tmux.conf:ro" '
            setup_cmd += "cp /tmp/user.tmux.conf ~/.tmux.conf && "

        # Add test bindings if provided
        if test_bindings:
            # Write test bindings to a temp file
            self._test_bindings_file = tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False)
            self._test_bindings_file.write(test_bindings)
            self._test_bindings_file.close()
            mounts += f'-v "{self._test_bindings_file.name}:/tmp/test.conf:ro" '
            if tmux_conf_path.exists():
                setup_cmd += 'echo "" >> ~/.tmux.conf && echo "# === NEW KEYBINDS TO TRY ===" >> ~/.tmux.conf && cat /tmp/test.conf >> ~/.tmux.conf && '
            else:
                setup_cmd += "cp /tmp/test.conf ~/.tmux.conf && "

        # Create challenge info file to mount
        challenge_text = ""
        if self._keybind_group:
            group = self._keybind_group
            challenge_text = f"=== PRACTICE: {group.name} ===\n{group.description}\n\nKeybinds to try:\n"
            for kb in group.keybinds:
                keybind = kb.get("keybind", "")
                desc = kb.get("description", "")
                cmd = kb.get("command", "")
                # Explain the keybind
                if keybind.startswith("M-"):
                    key_explain = f"Alt+{keybind[2:]}"
                else:
                    key_explain = f"prefix then {keybind}"
                challenge_text += f"\n  {keybind} ({key_explain})\n    {desc}\n    Command: {cmd}\n"
            challenge_text += f"\n{group.reasoning}\n"
        elif self._keybind_to_try:
            kb = self._keybind_to_try
            challenge_text = f"=== PRACTICE ===\nKeybind: {kb['keybind']}\nCommand: {kb['command']}\nDescription: {kb['description']}\n"
            if self._challenge:
                challenge_text += f"\nObjective: {self._challenge.get('objective', '')}\nHint: {self._challenge.get('hint', '')}\n"

        if challenge_text:
            self._challenge_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            self._challenge_file.write(challenge_text)
            self._challenge_file.close()
            mounts += f'-v "{self._challenge_file.name}:/home/learner/CHALLENGE.txt:ro" '
            # Show challenge on tmux startup
            setup_cmd += 'cat ~/CHALLENGE.txt && echo "Press Enter to start tmux..." && read && '

        # Check if pre-warmed container is available
        use_prewarm = self._is_prewarm_ready()
        prewarm_name = getattr(self.app, "PREWARM_CONTAINER_NAME", "moobler-prewarm")

        if use_prewarm:
            # Build setup command for pre-warmed container
            prewarm_setup = ""

            # Add test bindings to existing config
            if self._test_bindings_file:
                # Copy test bindings from host to container
                prewarm_setup += f'docker cp "{self._test_bindings_file.name}" {prewarm_name}:/tmp/test.conf && '
                prewarm_setup += f'docker exec {prewarm_name} bash -c \'echo "" >> ~/.tmux.conf && echo "# === NEW KEYBINDS TO TRY ===" >> ~/.tmux.conf && cat /tmp/test.conf >> ~/.tmux.conf\' && '

            # Copy challenge file if present
            if challenge_text and hasattr(self, '_challenge_file'):
                prewarm_setup += f'docker cp "{self._challenge_file.name}" {prewarm_name}:/home/learner/CHALLENGE.txt && '

            script = f'''#!/bin/bash
{challenge_display}

echo "Using pre-warmed container (fast startup)..."

# Setup test bindings in pre-warmed container
{prewarm_setup}

# Attach to pre-warmed container and start tmux
docker exec -it -e TERM=xterm-256color {prewarm_name} bash -c 'cat ~/CHALLENGE.txt 2>/dev/null; echo "Press Enter to start tmux..."; read; tmux new-session -s sandbox'

echo ""
echo "Sandbox exited. Press Enter to close..."
read
'''
        else:
            # Cold start - need to run new container
            script = f'''#!/bin/bash
{challenge_display}

# Clean up any stale container first
docker rm -f tmux-sandbox 2>/dev/null

echo "Starting sandbox container..."
echo "(Loading your tmux config + new keybinds)"

# Start container with user's config mounted
docker run -it --rm --name tmux-sandbox \\
    -e TERM=xterm-256color \\
    {mounts}\\
    --entrypoint /bin/bash \\
    tmux-learn-sandbox \\
    -c '{setup_cmd}tmux new-session -s sandbox'

echo ""
echo "Sandbox exited. Press Enter to close..."
read
'''
        return script

    def _launch_sandbox_kitty(self, user_config: str | None, test_bindings: str) -> bool:
        """Launch sandbox in a new Kitty window with everything self-contained."""
        if not shutil.which("kitty"):
            return False

        try:
            use_prewarm = self._is_prewarm_ready()
            script = self._build_sandbox_script(user_config, test_bindings)

            # Launch kitty fullscreen with the script
            subprocess.Popen([
                "kitty", "--start-as=fullscreen", "--title", "moobler sandbox",
                "bash", "-c", script
            ])

            self._log("")
            if use_prewarm:
                self._log("Opened sandbox in new Kitty window (pre-warmed - instant!)")
            else:
                self._log("Opened sandbox in new Kitty window")
            self._log("Switch to that window to practice")
            self._log("Exit tmux (type 'exit') when done")
            return True

        except Exception as e:
            self._log(f"Could not launch Kitty: {e}")
            return False

    async def _start_sandbox(self) -> None:
        """Start the Docker sandbox."""
        self._update_status("Launching sandbox...")
        self._log("")
        self._log("=" * 50)
        self._log("Launching tmux sandbox...")
        self._log("=" * 50)

        # Get user's current config
        user_config = None
        tmux_conf = Path.home() / ".tmux.conf"
        if tmux_conf.exists():
            user_config = tmux_conf.read_text()
            self._log(f"Will use your config from {tmux_conf}")

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

            # Launch sandbox in Kitty (self-contained - starts container, attaches, cleans up)
            used_prewarm = self._is_prewarm_ready()
            if self._launch_sandbox_kitty(user_config, test_bindings):
                self._update_status("Sandbox launched in Kitty")
                if self._keybind_to_try:
                    self._log("")
                    self._log(f"Try your new keybind: {self._keybind_to_try['keybind']}")
                    self._log(f"It should: {self._keybind_to_try['description']}")
                self._log("")
                self._log("The Kitty window handles everything:")
                self._log("  - Container starts automatically")
                self._log("  - Exit tmux to stop and clean up")

                # If we used pre-warmed container, mark it as used (dirty)
                # so subsequent launches use cold start instead
                if used_prewarm:
                    self._mark_prewarm_used()
            else:
                # Fallback: show manual instructions
                self._log("")
                self._log("Could not launch Kitty. Manual steps:")
                self._log("")
                self._log("1. Open a new terminal")
                self._log("2. Run: docker run -it --rm --name tmux-sandbox tmux-learn-sandbox")
                self._log("")
                if self._keybind_to_try:
                    self._log(f"Try your new keybind: {self._keybind_to_try['keybind']}")
                    self._log(f"It should: {self._keybind_to_try['description']}")
                self._update_status("Manual launch required")

        except Exception as e:
            self._log(f"ERROR: {e}")
            self._update_status("Error starting sandbox")

    async def _stop_sandbox(self) -> None:
        """Stop the Docker sandbox."""
        self._update_status("Stopping container...")
        self._log("")
        self._log("Stopping sandbox...")

        try:
            # Try to stop via manager first
            await self._container_manager.stop()
            self._log("Container stopped.")
        except Exception:
            pass

        # Also try direct docker stop in case it was started by Kitty script
        try:
            subprocess.run(
                ["docker", "stop", "tmux-sandbox"],
                capture_output=True,
                timeout=5
            )
            self._log("Container stopped and removed.")
        except Exception:
            pass

        self._update_status("Not running")
        self._log("Ready to start a new sandbox.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-back":
            self.app.switch_screen("home")
        elif event.button.id == "btn-start":
            self.run_worker(self._start_sandbox())
        elif event.button.id == "btn-stop":
            self.run_worker(self._stop_sandbox())
        elif event.button.id == "btn-apply":
            self.run_worker(self._apply_to_config())

    async def _apply_to_config(self) -> None:
        """Add keybind(s) to user's tmux.conf."""
        # Handle group
        if self._keybind_group:
            try:
                from ...ai.smart_suggester import SmartSuggester
                suggester = SmartSuggester()

                success, msg = await suggester.add_group_to_config(self._keybind_group)

                if success:
                    self._log("")
                    self._log("=" * 50)
                    self._log("ADDED TO CONFIG")
                    self._log("=" * 50)
                    self._log(msg)
                    self._log("")
                    self._log("Run 'tmux source ~/.tmux.conf' to reload")
                    self.app.notify(msg, title="Config Updated")
                else:
                    self._log(f"Error: {msg}")
                    self.app.notify(msg, title="Error")
            except Exception as e:
                self._log(f"Error adding to config: {e}")
                self.app.notify(f"Error: {e}", title="Error")
            return

        # Handle single keybind
        if self._keybind_to_try:
            try:
                from ...config.merger import ConfigMerger
                merger = ConfigMerger()

                kb = self._keybind_to_try
                from ...config.models import BindingMode

                # Determine binding mode
                mode = BindingMode.ROOT if kb["keybind"].startswith("M-") else BindingMode.PREFIX

                success, msg = merger.add_keybinding(
                    keybind=kb["keybind"],
                    command=kb["command"],
                    description=kb.get("description", ""),
                    mode=mode,
                )

                if success:
                    self._log("")
                    self._log("=" * 50)
                    self._log("ADDED TO CONFIG")
                    self._log("=" * 50)
                    self._log(msg)
                    self._log("")
                    self._log("Run 'tmux source ~/.tmux.conf' to reload")
                    self.app.notify(msg, title="Config Updated")
                else:
                    self._log(f"Error: {msg}")
                    self.app.notify(msg, title="Error")
            except Exception as e:
                self._log(f"Error adding to config: {e}")
                self.app.notify(f"Error: {e}", title="Error")
            return

        self.app.notify(
            "No keybind selected. Go to Discover (3) first.",
            title="No Keybind",
        )

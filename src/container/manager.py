"""Docker container manager for tmux sandbox."""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

import docker
from docker.models.containers import Container


class ContainerManager:
    """Manages Docker containers for tmux sandbox environments."""

    IMAGE_NAME = "tmux-learn-sandbox"
    CONTAINER_NAME = "tmux-sandbox"

    def __init__(self):
        """Initialize the container manager."""
        self._client: Optional[docker.DockerClient] = None
        self._container: Optional[Container] = None

    @property
    def client(self) -> docker.DockerClient:
        """Get or create Docker client."""
        if self._client is None:
            self._client = docker.from_env()
        return self._client

    def is_image_built(self) -> bool:
        """Check if the sandbox image exists."""
        try:
            self.client.images.get(self.IMAGE_NAME)
            return True
        except docker.errors.ImageNotFound:
            return False

    async def build_image(self, dockerfile_path: Optional[Path] = None) -> None:
        """Build the sandbox Docker image.

        Args:
            dockerfile_path: Path to Dockerfile directory. Uses default if not specified.
        """
        if dockerfile_path is None:
            # Look for Dockerfile in package
            dockerfile_path = Path(__file__).parent.parent.parent / "docker"

        if not dockerfile_path.exists():
            raise FileNotFoundError(f"Dockerfile directory not found: {dockerfile_path}")

        # Build in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.client.images.build(
                path=str(dockerfile_path),
                tag=self.IMAGE_NAME,
                rm=True,
            ),
        )

    def is_running(self) -> bool:
        """Check if sandbox container is running."""
        try:
            container = self.client.containers.get(self.CONTAINER_NAME)
            return container.status == "running"
        except docker.errors.NotFound:
            return False

    async def start(
        self,
        user_config: Optional[str] = None,
        test_bindings: Optional[str] = None,
    ) -> str:
        """Start the sandbox container.

        Args:
            user_config: User's tmux.conf content to include
            test_bindings: New keybindings to test

        Returns:
            Container ID
        """
        # Build image if needed
        if not self.is_image_built():
            await self.build_image()

        # Stop any existing container
        await self.stop()

        # Prepare volume mounts
        volumes = {}
        tmpdir = Path(tempfile.gettempdir()) / "tmux-learn"
        tmpdir.mkdir(exist_ok=True)

        if user_config:
            user_conf_path = tmpdir / "user-tmux.conf"
            user_conf_path.write_text(user_config)
            volumes[str(user_conf_path)] = {"bind": "/tmp/user-tmux.conf", "mode": "ro"}

        if test_bindings:
            test_conf_path = tmpdir / "test-bindings.conf"
            test_conf_path.write_text(test_bindings)
            volumes[str(test_conf_path)] = {"bind": "/tmp/test-bindings.conf", "mode": "ro"}

        # Start container
        loop = asyncio.get_event_loop()
        self._container = await loop.run_in_executor(
            None,
            lambda: self.client.containers.run(
                self.IMAGE_NAME,
                name=self.CONTAINER_NAME,
                detach=True,
                tty=True,
                stdin_open=True,
                volumes=volumes,
                remove=True,
            ),
        )

        return self._container.id

    async def stop(self) -> None:
        """Stop and remove the sandbox container."""
        try:
            container = self.client.containers.get(self.CONTAINER_NAME)
            container.stop(timeout=5)
        except docker.errors.NotFound:
            pass  # Container doesn't exist
        except Exception:
            # Force remove if stop fails
            try:
                container = self.client.containers.get(self.CONTAINER_NAME)
                container.remove(force=True)
            except docker.errors.NotFound:
                pass

        self._container = None

    def get_attach_command(self) -> str:
        """Get the command to attach to the sandbox."""
        return f"docker exec -it {self.CONTAINER_NAME} tmux attach-session -t learn"

    async def exec_command(self, command: str) -> tuple[int, str]:
        """Execute a command in the container.

        Args:
            command: Command to execute

        Returns:
            Tuple of (exit_code, output)
        """
        if not self.is_running():
            raise RuntimeError("Container is not running")

        container = self.client.containers.get(self.CONTAINER_NAME)
        result = container.exec_run(command)
        return result.exit_code, result.output.decode("utf-8")

    async def send_keys(self, keys: str, pane: int = 0) -> None:
        """Send keys to tmux in the container.

        Args:
            keys: Keys to send (tmux format)
            pane: Target pane number
        """
        await self.exec_command(f"tmux send-keys -t learn:{pane} {keys}")

    async def get_pane_contents(self, pane: int = 0) -> str:
        """Get the contents of a tmux pane.

        Args:
            pane: Pane number

        Returns:
            Pane content as string
        """
        _, output = await self.exec_command(
            f"tmux capture-pane -t learn:{pane} -p"
        )
        return output

    def get_status(self) -> dict:
        """Get container status information."""
        try:
            container = self.client.containers.get(self.CONTAINER_NAME)
            return {
                "running": container.status == "running",
                "id": container.short_id,
                "status": container.status,
                "image": self.IMAGE_NAME,
            }
        except docker.errors.NotFound:
            return {
                "running": False,
                "id": None,
                "status": "not created",
                "image": self.IMAGE_NAME,
            }

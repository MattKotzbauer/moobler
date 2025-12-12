"""Challenge execution engine."""

import asyncio
from datetime import datetime
from typing import Optional, Callable, Awaitable

from .types import Challenge, BUILTIN_CHALLENGES
from ..container.manager import ContainerManager
from ..container.tmux_bridge import TmuxBridge


class ChallengeResult:
    """Result of a challenge attempt."""

    def __init__(
        self,
        challenge: Challenge,
        success: bool,
        message: str,
        time_taken: float,
        attempts: int = 1,
    ):
        self.challenge = challenge
        self.success = success
        self.message = message
        self.time_taken = time_taken
        self.attempts = attempts
        self.timestamp = datetime.now()


class ChallengeEngine:
    """Engine for running interactive challenges."""

    def __init__(
        self,
        container_manager: Optional[ContainerManager] = None,
    ):
        """Initialize the challenge engine.

        Args:
            container_manager: Container manager for sandbox
        """
        self.manager = container_manager or ContainerManager()
        self.bridge: Optional[TmuxBridge] = None
        self._current_challenge: Optional[Challenge] = None
        self._initial_state: Optional[dict] = None
        self._on_progress: Optional[Callable[[str], Awaitable[None]]] = None

    def get_challenges(
        self,
        difficulty: Optional[str] = None,
        challenge_type: Optional[str] = None,
    ) -> list[Challenge]:
        """Get available challenges.

        Args:
            difficulty: Filter by difficulty
            challenge_type: Filter by type

        Returns:
            List of matching challenges
        """
        challenges = BUILTIN_CHALLENGES.copy()

        if difficulty:
            challenges = [c for c in challenges if c.difficulty == difficulty]
        if challenge_type:
            challenges = [c for c in challenges if c.type.value == challenge_type]

        return challenges

    def get_challenge_by_id(self, challenge_id: str) -> Optional[Challenge]:
        """Get a specific challenge by ID."""
        for challenge in BUILTIN_CHALLENGES:
            if challenge.id == challenge_id:
                return challenge
        return None

    async def start_challenge(
        self,
        challenge: Challenge,
        on_progress: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> None:
        """Start a challenge.

        Args:
            challenge: The challenge to start
            on_progress: Callback for progress updates
        """
        self._on_progress = on_progress
        self._current_challenge = challenge

        # Ensure container is running
        if not self.manager.is_running():
            await self._notify("Starting sandbox container...")
            await self.manager.start()

        # Create bridge
        self.bridge = TmuxBridge(self.manager)

        # Set up challenge environment
        await self._notify(f"Setting up: {challenge.name}")
        await self.bridge.setup_challenge(challenge.setup.model_dump())

        # Capture initial state
        self._initial_state = await self.bridge.get_current_state()

        await self._notify(f"Objective: {challenge.objective}")
        await self._notify(f"Hint: {challenge.hint}")
        await self._notify("")
        await self._notify(f"Connect to sandbox: {self.manager.get_attach_command()}")

    async def check_completion(self) -> Optional[ChallengeResult]:
        """Check if the current challenge is completed.

        Returns:
            ChallengeResult if completed, None otherwise
        """
        if not self._current_challenge or not self.bridge:
            return None

        success, message = await self.bridge.verify_challenge(
            self._current_challenge.expectation.model_dump(),
            self._initial_state or {},
        )

        if success:
            return ChallengeResult(
                challenge=self._current_challenge,
                success=True,
                message=message,
                time_taken=0,  # TODO: track time
            )

        return None

    async def run_challenge_loop(
        self,
        challenge: Challenge,
        timeout: float = 300.0,
        check_interval: float = 1.0,
    ) -> ChallengeResult:
        """Run a challenge with automatic completion checking.

        Args:
            challenge: The challenge to run
            timeout: Maximum time in seconds
            check_interval: How often to check completion

        Returns:
            ChallengeResult
        """
        await self.start_challenge(challenge)

        start_time = asyncio.get_event_loop().time()
        attempts = 0

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time

            if elapsed > timeout:
                return ChallengeResult(
                    challenge=challenge,
                    success=False,
                    message="Time's up! Try again.",
                    time_taken=elapsed,
                    attempts=attempts,
                )

            result = await self.check_completion()
            if result:
                result.time_taken = elapsed
                result.attempts = attempts
                return result

            attempts += 1
            await asyncio.sleep(check_interval)

    async def end_challenge(self) -> None:
        """Clean up after a challenge."""
        self._current_challenge = None
        self._initial_state = None
        self.bridge = None

    async def _notify(self, message: str) -> None:
        """Send a progress notification."""
        if self._on_progress:
            await self._on_progress(message)

    def get_challenge_for_keybind(self, keybind: str) -> Optional[Challenge]:
        """Find a challenge that teaches a specific keybind.

        Args:
            keybind: The keybind to learn

        Returns:
            A matching challenge, or None
        """
        for challenge in BUILTIN_CHALLENGES:
            if challenge.keybind == keybind:
                return challenge
        return None

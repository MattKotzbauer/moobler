"""Challenge type definitions."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ChallengeType(str, Enum):
    """Types of challenges."""

    NAVIGATION = "navigation"
    RESIZE = "resize"
    SPLIT = "split"
    COPY = "copy"
    SESSION = "session"
    WINDOW = "window"
    CUSTOM = "custom"


class ChallengeSetup(BaseModel):
    """Setup configuration for a challenge."""

    panes: int = Field(default=1, description="Number of panes to create")
    windows: int = Field(default=1, description="Number of windows to create")
    layout: str = Field(default="tiled", description="Tmux layout to use")
    start_pane: int = Field(default=0, description="Starting pane index")
    start_window: int = Field(default=0, description="Starting window index")
    content: Optional[str] = Field(default=None, description="Content to display")


class ChallengeExpectation(BaseModel):
    """Expected state after challenge completion."""

    target_pane: Optional[int] = Field(default=None)
    target_window: Optional[int] = Field(default=None)
    min_panes: Optional[int] = Field(default=None)
    min_windows: Optional[int] = Field(default=None)
    check_resize: bool = Field(default=False)
    check_copy: bool = Field(default=False)


class Challenge(BaseModel):
    """A learning challenge."""

    id: str
    name: str
    description: str
    type: ChallengeType
    keybind: str = Field(description="The keybind being practiced")
    command: str = Field(description="The tmux command")
    objective: str = Field(description="What the user needs to do")
    setup: ChallengeSetup = Field(default_factory=ChallengeSetup)
    expectation: ChallengeExpectation = Field(default_factory=ChallengeExpectation)
    hint: str = Field(default="")
    difficulty: str = Field(default="beginner")
    time_limit: Optional[int] = Field(default=None, description="Time limit in seconds")

    @classmethod
    def from_dict(cls, data: dict) -> "Challenge":
        """Create a Challenge from a dictionary (e.g., from AI generation)."""
        # Map AI-generated format to our model
        setup_data = data.get("setup", {})
        setup = ChallengeSetup(**setup_data) if isinstance(setup_data, dict) else ChallengeSetup()

        # Parse success criteria into expectations
        expectation = ChallengeExpectation()
        success = data.get("success_criteria", "")
        if "pane" in success.lower() and "target_pane" in setup_data:
            expectation.target_pane = setup_data.get("target_pane")
        if "window" in success.lower():
            expectation.target_window = setup_data.get("target_window")
        if "split" in success.lower() or "panes" in success.lower():
            expectation.min_panes = setup_data.get("panes", 1) + 1
        if "resize" in success.lower():
            expectation.check_resize = True

        return cls(
            id=data.get("id", "generated"),
            name=data.get("name", data.get("objective", "Challenge")),
            description=data.get("description", ""),
            type=ChallengeType.CUSTOM,
            keybind=data.get("keybind", ""),
            command=data.get("command", ""),
            objective=data.get("objective", ""),
            setup=setup,
            expectation=expectation,
            hint=data.get("hint", ""),
            difficulty=data.get("difficulty", "beginner"),
        )


# Pre-built challenges
BUILTIN_CHALLENGES = [
    Challenge(
        id="nav-pane-left",
        name="Navigate Left",
        description="Practice moving to the pane on the left",
        type=ChallengeType.NAVIGATION,
        keybind="M-h",
        command="select-pane -L",
        objective="Move to the pane on the left",
        setup=ChallengeSetup(panes=4, layout="tiled", start_pane=1),
        expectation=ChallengeExpectation(target_pane=0),
        hint="Press Alt+h to move left",
        difficulty="beginner",
    ),
    Challenge(
        id="nav-pane-right",
        name="Navigate Right",
        description="Practice moving to the pane on the right",
        type=ChallengeType.NAVIGATION,
        keybind="M-l",
        command="select-pane -R",
        objective="Move to the pane on the right",
        setup=ChallengeSetup(panes=4, layout="tiled", start_pane=0),
        expectation=ChallengeExpectation(target_pane=1),
        hint="Press Alt+l to move right",
        difficulty="beginner",
    ),
    Challenge(
        id="split-horizontal",
        name="Split Horizontally",
        description="Create a side-by-side split",
        type=ChallengeType.SPLIT,
        keybind="prefix + |",
        command="split-window -h",
        objective="Split the current pane horizontally (side by side)",
        setup=ChallengeSetup(panes=1),
        expectation=ChallengeExpectation(min_panes=2),
        hint="Press your prefix key, then |",
        difficulty="beginner",
    ),
    Challenge(
        id="split-vertical",
        name="Split Vertically",
        description="Create a top-bottom split",
        type=ChallengeType.SPLIT,
        keybind="prefix + -",
        command="split-window -v",
        objective="Split the current pane vertically (top and bottom)",
        setup=ChallengeSetup(panes=1),
        expectation=ChallengeExpectation(min_panes=2),
        hint="Press your prefix key, then -",
        difficulty="beginner",
    ),
    Challenge(
        id="resize-pane",
        name="Resize Pane",
        description="Make one pane larger",
        type=ChallengeType.RESIZE,
        keybind="M-H",
        command="resize-pane -L 5",
        objective="Resize the current pane to the left",
        setup=ChallengeSetup(panes=2, layout="even-horizontal"),
        expectation=ChallengeExpectation(check_resize=True),
        hint="Press Alt+Shift+h to resize left",
        difficulty="intermediate",
    ),
    Challenge(
        id="window-switch",
        name="Switch Window",
        description="Jump to another window",
        type=ChallengeType.WINDOW,
        keybind="M-2",
        command="select-window -t 2",
        objective="Switch to window 2",
        setup=ChallengeSetup(windows=3, start_window=1),
        expectation=ChallengeExpectation(target_window=2),
        hint="Press Alt+2 to jump to window 2",
        difficulty="beginner",
    ),
]

"""Pydantic models for tmux configuration."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class KeyModifier(str, Enum):
    """Key modifiers used in tmux bindings."""

    CTRL = "C"
    META = "M"  # Alt key
    SHIFT = "S"
    NONE = ""


class BindingMode(str, Enum):
    """Tmux binding modes."""

    PREFIX = "prefix"  # Requires prefix key first
    ROOT = "root"  # No prefix needed (-n flag)
    COPY_MODE = "copy-mode"
    COPY_MODE_VI = "copy-mode-vi"


class Keybinding(BaseModel):
    """Represents a single tmux keybinding."""

    key: str = Field(description="The key (e.g., 'h', 'Left', 'Space')")
    modifiers: list[KeyModifier] = Field(default_factory=list)
    command: str = Field(description="The tmux command to execute")
    mode: BindingMode = Field(default=BindingMode.PREFIX)
    description: Optional[str] = Field(default=None)
    raw_line: str = Field(description="Original line from config")

    @property
    def key_combo(self) -> str:
        """Return human-readable key combination like 'M-h' or 'C-a'."""
        if not self.modifiers or self.modifiers == [KeyModifier.NONE]:
            return self.key
        mods = "-".join(m.value for m in self.modifiers if m != KeyModifier.NONE)
        return f"{mods}-{self.key}"

    @property
    def is_navigation(self) -> bool:
        """Check if this is a navigation-related binding."""
        nav_commands = [
            "select-pane",
            "select-window",
            "next-window",
            "previous-window",
            "last-window",
            "switch-client",
        ]
        return any(cmd in self.command for cmd in nav_commands)

    @property
    def is_resize(self) -> bool:
        """Check if this is a resize-related binding."""
        return "resize-pane" in self.command

    @property
    def is_split(self) -> bool:
        """Check if this is a split-related binding."""
        return "split-window" in self.command or "split" in self.command


class UserStyle(BaseModel):
    """Detected user preferences and patterns."""

    prefix_key: str = Field(default="C-b", description="The prefix key")
    uses_vim_keys: bool = Field(default=False, description="Uses h/j/k/l navigation")
    uses_arrow_keys: bool = Field(default=False, description="Uses arrow key navigation")
    prefers_meta: bool = Field(default=False, description="Prefers Meta/Alt bindings")
    prefers_ctrl: bool = Field(default=False, description="Prefers Ctrl bindings")
    navigation_pattern: Optional[str] = Field(
        default=None, description="Detected navigation key pattern (e.g., 'M-hjkl')"
    )


class TmuxConfig(BaseModel):
    """Complete parsed tmux configuration."""

    path: str = Field(description="Path to the config file")
    keybindings: list[Keybinding] = Field(default_factory=list)
    raw_options: dict[str, str] = Field(
        default_factory=dict, description="Non-binding options like set-option"
    )
    style: UserStyle = Field(default_factory=UserStyle)

    def get_bindings_for_mode(self, mode: BindingMode) -> list[Keybinding]:
        """Get all keybindings for a specific mode."""
        return [kb for kb in self.keybindings if kb.mode == mode]

    def get_navigation_bindings(self) -> list[Keybinding]:
        """Get all navigation-related keybindings."""
        return [kb for kb in self.keybindings if kb.is_navigation]

    def has_binding(self, key_combo: str, mode: BindingMode = BindingMode.PREFIX) -> bool:
        """Check if a specific key combination is already bound."""
        return any(
            kb.key_combo == key_combo and kb.mode == mode for kb in self.keybindings
        )

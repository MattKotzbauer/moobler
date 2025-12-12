"""Curated database of tmux tips and keybindings."""

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class CuratedTip(BaseModel):
    """A curated tmux tip or keybinding."""

    id: str
    category: str
    name: str
    description: str
    keybind: str
    command: str
    difficulty: str = Field(default="beginner")  # beginner, intermediate, advanced
    tags: list[str] = Field(default_factory=list)
    related_to: list[str] = Field(default_factory=list)  # Related tip IDs
    vim_style: bool = Field(default=False)
    requires_prefix: bool = Field(default=True)


# Built-in curated tips
CURATED_TIPS: list[dict] = [
    # Navigation
    {
        "id": "nav-pane-hjkl",
        "category": "navigation",
        "name": "Vim-style Pane Navigation",
        "description": "Navigate between panes using h/j/k/l keys (left/down/up/right)",
        "keybind": "prefix + h/j/k/l",
        "command": "bind h select-pane -L; bind j select-pane -D; bind k select-pane -U; bind l select-pane -R",
        "difficulty": "beginner",
        "tags": ["vim", "navigation", "panes"],
        "vim_style": True,
    },
    {
        "id": "nav-pane-meta-hjkl",
        "category": "navigation",
        "name": "Alt+hjkl Pane Navigation (No Prefix)",
        "description": "Navigate panes instantly with Alt+h/j/k/l - no prefix needed",
        "keybind": "M-h/j/k/l",
        "command": "bind -n M-h select-pane -L; bind -n M-j select-pane -D; bind -n M-k select-pane -U; bind -n M-l select-pane -R",
        "difficulty": "beginner",
        "tags": ["vim", "navigation", "panes", "no-prefix"],
        "vim_style": True,
        "requires_prefix": False,
    },
    {
        "id": "nav-window-number",
        "category": "navigation",
        "name": "Quick Window Switch with Alt+Number",
        "description": "Jump to windows 1-9 instantly with Alt+1 through Alt+9",
        "keybind": "M-1..9",
        "command": "bind -n M-1 select-window -t 1; bind -n M-2 select-window -t 2; ...",
        "difficulty": "beginner",
        "tags": ["navigation", "windows", "no-prefix"],
        "requires_prefix": False,
    },
    {
        "id": "nav-last-window",
        "category": "navigation",
        "name": "Toggle Last Window",
        "description": "Quickly switch between your two most recent windows",
        "keybind": "prefix + Tab",
        "command": "bind Tab last-window",
        "difficulty": "beginner",
        "tags": ["navigation", "windows"],
    },
    # Resize
    {
        "id": "resize-hjkl",
        "category": "resize",
        "name": "Vim-style Pane Resize",
        "description": "Resize panes with H/J/K/L (capital letters)",
        "keybind": "prefix + H/J/K/L",
        "command": "bind H resize-pane -L 5; bind J resize-pane -D 5; bind K resize-pane -U 5; bind L resize-pane -R 5",
        "difficulty": "intermediate",
        "tags": ["vim", "resize", "panes"],
        "vim_style": True,
        "related_to": ["nav-pane-hjkl"],
    },
    {
        "id": "resize-meta-hjkl",
        "category": "resize",
        "name": "Alt+Shift+hjkl Pane Resize (No Prefix)",
        "description": "Resize panes instantly with Alt+Shift+h/j/k/l",
        "keybind": "M-H/J/K/L",
        "command": "bind -n M-H resize-pane -L 5; bind -n M-J resize-pane -D 5; bind -n M-K resize-pane -U 5; bind -n M-L resize-pane -R 5",
        "difficulty": "intermediate",
        "tags": ["vim", "resize", "panes", "no-prefix"],
        "vim_style": True,
        "requires_prefix": False,
        "related_to": ["nav-pane-meta-hjkl"],
    },
    # Splits
    {
        "id": "split-visual",
        "category": "panes",
        "name": "Visual Split Keys",
        "description": "Use | for horizontal split and - for vertical (visual mnemonics)",
        "keybind": "prefix + | and prefix + -",
        "command": "bind | split-window -h -c '#{pane_current_path}'; bind - split-window -v -c '#{pane_current_path}'",
        "difficulty": "beginner",
        "tags": ["panes", "splits"],
    },
    {
        "id": "split-current-path",
        "category": "panes",
        "name": "Split in Current Directory",
        "description": "New splits open in the same directory as current pane",
        "keybind": "prefix + \" and prefix + %",
        "command": "bind '\"' split-window -v -c '#{pane_current_path}'; bind % split-window -h -c '#{pane_current_path}'",
        "difficulty": "beginner",
        "tags": ["panes", "splits", "paths"],
    },
    # Copy mode
    {
        "id": "copy-vim-mode",
        "category": "copy",
        "name": "Vim Copy Mode",
        "description": "Use vi-style keys in copy mode (v to select, y to yank)",
        "keybind": "v/y in copy mode",
        "command": "setw -g mode-keys vi; bind -T copy-mode-vi v send -X begin-selection; bind -T copy-mode-vi y send -X copy-selection-and-cancel",
        "difficulty": "intermediate",
        "tags": ["vim", "copy", "clipboard"],
        "vim_style": True,
    },
    {
        "id": "copy-mouse",
        "category": "copy",
        "name": "Mouse Copy Support",
        "description": "Select text with mouse and copy to clipboard",
        "keybind": "Mouse drag",
        "command": "set -g mouse on; bind -T copy-mode-vi MouseDragEnd1Pane send -X copy-pipe-and-cancel 'xclip -selection clipboard'",
        "difficulty": "beginner",
        "tags": ["mouse", "copy", "clipboard"],
    },
    # Session management
    {
        "id": "session-picker",
        "category": "session",
        "name": "Interactive Session Picker",
        "description": "Visual tree view to switch between sessions and windows",
        "keybind": "prefix + s",
        "command": "bind s choose-tree -s",
        "difficulty": "beginner",
        "tags": ["sessions", "navigation"],
    },
    {
        "id": "session-new",
        "category": "session",
        "name": "Quick New Session",
        "description": "Create a new session with a name prompt",
        "keybind": "prefix + S",
        "command": "bind S command-prompt -p 'New session:' 'new-session -s %%'",
        "difficulty": "beginner",
        "tags": ["sessions"],
    },
    # Productivity
    {
        "id": "reload-config",
        "category": "productivity",
        "name": "Reload Config",
        "description": "Reload tmux.conf without restarting",
        "keybind": "prefix + r",
        "command": "bind r source-file ~/.tmux.conf \\; display 'Config reloaded!'",
        "difficulty": "beginner",
        "tags": ["config", "productivity"],
    },
    {
        "id": "pane-zoom",
        "category": "productivity",
        "name": "Zoom Pane Toggle",
        "description": "Temporarily maximize a pane, press again to restore",
        "keybind": "prefix + z",
        "command": "bind z resize-pane -Z",
        "difficulty": "beginner",
        "tags": ["panes", "productivity"],
    },
    {
        "id": "pane-sync",
        "category": "productivity",
        "name": "Synchronize Panes",
        "description": "Type in all panes simultaneously (great for multi-server)",
        "keybind": "prefix + e",
        "command": "bind e setw synchronize-panes",
        "difficulty": "advanced",
        "tags": ["panes", "productivity", "advanced"],
    },
    {
        "id": "kill-pane-confirm",
        "category": "productivity",
        "name": "Kill Pane with Confirmation",
        "description": "Close current pane with a confirmation prompt",
        "keybind": "prefix + x",
        "command": "bind x confirm-before -p 'Kill pane? (y/n)' kill-pane",
        "difficulty": "beginner",
        "tags": ["panes", "safety"],
    },
    # Status bar
    {
        "id": "status-position",
        "category": "appearance",
        "name": "Status Bar Position",
        "description": "Move status bar to top or bottom",
        "keybind": "N/A (option)",
        "command": "set -g status-position top",
        "difficulty": "beginner",
        "tags": ["appearance", "status"],
    },
    # Mouse
    {
        "id": "mouse-enable",
        "category": "mouse",
        "name": "Enable Mouse Support",
        "description": "Click to select panes, resize with drag, scroll history",
        "keybind": "Mouse",
        "command": "set -g mouse on",
        "difficulty": "beginner",
        "tags": ["mouse", "navigation"],
    },
]


def get_curated_tips(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    vim_only: bool = False,
    no_prefix_only: bool = False,
) -> list[CuratedTip]:
    """Get curated tips with optional filtering.

    Args:
        category: Filter by category (navigation, resize, panes, etc.)
        difficulty: Filter by difficulty (beginner, intermediate, advanced)
        vim_only: Only return vim-style tips
        no_prefix_only: Only return tips that don't require prefix

    Returns:
        List of matching CuratedTip objects
    """
    tips = [CuratedTip(**tip) for tip in CURATED_TIPS]

    if category:
        tips = [t for t in tips if t.category == category]
    if difficulty:
        tips = [t for t in tips if t.difficulty == difficulty]
    if vim_only:
        tips = [t for t in tips if t.vim_style]
    if no_prefix_only:
        tips = [t for t in tips if not t.requires_prefix]

    return tips


def get_tip_by_id(tip_id: str) -> Optional[CuratedTip]:
    """Get a specific tip by ID."""
    for tip in CURATED_TIPS:
        if tip["id"] == tip_id:
            return CuratedTip(**tip)
    return None


def get_related_tips(tip: CuratedTip) -> list[CuratedTip]:
    """Get tips related to a given tip."""
    related = []
    for related_id in tip.related_to:
        if related_tip := get_tip_by_id(related_id):
            related.append(related_tip)
    return related


def get_categories() -> list[str]:
    """Get all available categories."""
    return list(set(tip["category"] for tip in CURATED_TIPS))


def save_tips_to_json(path: Path) -> None:
    """Save tips to a JSON file."""
    path.write_text(json.dumps(CURATED_TIPS, indent=2))


def load_tips_from_json(path: Path) -> list[CuratedTip]:
    """Load tips from a JSON file."""
    data = json.loads(path.read_text())
    return [CuratedTip(**tip) for tip in data]

"""Parser for tmux configuration files."""

import re
from pathlib import Path
from typing import Optional

from .models import BindingMode, Keybinding, KeyModifier, TmuxConfig, UserStyle


def _parse_key_with_modifiers(key_str: str) -> tuple[str, list[KeyModifier]]:
    """Parse a key string like 'M-h' into key and modifiers."""
    modifiers = []
    key = key_str

    # Handle modifier prefixes (C-, M-, S-)
    pattern = r"^([CMS])-(.+)$"
    while match := re.match(pattern, key):
        mod_char = match.group(1)
        key = match.group(2)
        if mod_char == "C":
            modifiers.append(KeyModifier.CTRL)
        elif mod_char == "M":
            modifiers.append(KeyModifier.META)
        elif mod_char == "S":
            modifiers.append(KeyModifier.SHIFT)

    return key, modifiers if modifiers else [KeyModifier.NONE]


def _parse_bind_line(line: str) -> Optional[Keybinding]:
    """Parse a single bind/bind-key line."""
    line = line.strip()

    # Skip comments and empty lines
    if not line or line.startswith("#"):
        return None

    # Match bind-key or bind commands
    # Formats:
    #   bind-key [-n] [-T mode] key command
    #   bind [-n] [-T mode] key command
    bind_pattern = r"^(?:bind-key|bind)\s+(.+)$"
    match = re.match(bind_pattern, line)
    if not match:
        return None

    args = match.group(1)

    # Parse flags
    mode = BindingMode.PREFIX
    remaining = args

    # Check for -n (root mode, no prefix)
    if re.match(r"^-n\s+", remaining):
        mode = BindingMode.ROOT
        remaining = re.sub(r"^-n\s+", "", remaining)

    # Check for -T mode
    mode_match = re.match(r"^-T\s+(\S+)\s+", remaining)
    if mode_match:
        mode_name = mode_match.group(1)
        if mode_name == "copy-mode":
            mode = BindingMode.COPY_MODE
        elif mode_name == "copy-mode-vi":
            mode = BindingMode.COPY_MODE_VI
        elif mode_name == "root":
            mode = BindingMode.ROOT
        remaining = re.sub(r"^-T\s+\S+\s+", "", remaining)

    # Now remaining should be: key command [args...]
    # Handle quoted keys or simple keys
    if remaining.startswith('"') or remaining.startswith("'"):
        # Quoted key
        quote = remaining[0]
        end_quote = remaining.find(quote, 1)
        if end_quote == -1:
            return None
        key_str = remaining[1:end_quote]
        command = remaining[end_quote + 1 :].strip()
    else:
        # Simple key - first word
        parts = remaining.split(None, 1)
        if len(parts) < 2:
            return None
        key_str, command = parts

    key, modifiers = _parse_key_with_modifiers(key_str)

    return Keybinding(
        key=key,
        modifiers=modifiers,
        command=command,
        mode=mode,
        raw_line=line,
    )


def _parse_set_option(line: str) -> Optional[tuple[str, str]]:
    """Parse a set-option or set line."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None

    # Match set-option, set, setw, set-window-option
    set_pattern = r"^(?:set-option|set|setw|set-window-option)\s+(?:-g\s+)?(\S+)\s+(.+)$"
    match = re.match(set_pattern, line)
    if match:
        return match.group(1), match.group(2).strip("'\"")
    return None


def _detect_user_style(keybindings: list[Keybinding], options: dict[str, str]) -> UserStyle:
    """Analyze keybindings to detect user's preferred style."""
    style = UserStyle()

    # Get prefix key from options
    if "prefix" in options:
        style.prefix_key = options["prefix"]

    # Analyze navigation bindings
    nav_bindings = [kb for kb in keybindings if kb.is_navigation]

    vim_keys = {"h", "j", "k", "l"}
    arrow_keys = {"Left", "Right", "Up", "Down"}

    nav_keys = {kb.key for kb in nav_bindings}
    style.uses_vim_keys = bool(nav_keys & vim_keys)
    style.uses_arrow_keys = bool(nav_keys & arrow_keys)

    # Count modifier usage
    meta_count = sum(1 for kb in keybindings if KeyModifier.META in kb.modifiers)
    ctrl_count = sum(1 for kb in keybindings if KeyModifier.CTRL in kb.modifiers)
    root_count = sum(1 for kb in keybindings if kb.mode == BindingMode.ROOT)

    style.prefers_meta = meta_count > ctrl_count or root_count > len(keybindings) // 3

    # Detect navigation pattern
    if style.uses_vim_keys:
        meta_vim = [
            kb
            for kb in nav_bindings
            if kb.key in vim_keys and KeyModifier.META in kb.modifiers
        ]
        if len(meta_vim) >= 3:
            style.navigation_pattern = "M-hjkl"

        root_vim = [
            kb for kb in nav_bindings if kb.key in vim_keys and kb.mode == BindingMode.ROOT
        ]
        if len(root_vim) >= 3 and not style.navigation_pattern:
            style.navigation_pattern = "hjkl (root)"

    return style


def parse_tmux_config(path: Optional[str] = None) -> TmuxConfig:
    """Parse a tmux configuration file.

    Args:
        path: Path to tmux.conf. If None, tries ~/.tmux.conf

    Returns:
        Parsed TmuxConfig object
    """
    if path is None:
        path = str(Path.home() / ".tmux.conf")

    config_path = Path(path)
    keybindings: list[Keybinding] = []
    options: dict[str, str] = {}

    if config_path.exists():
        content = config_path.read_text()

        for line in content.splitlines():
            # Try parsing as keybinding
            if kb := _parse_bind_line(line):
                keybindings.append(kb)
                continue

            # Try parsing as option
            if opt := _parse_set_option(line):
                options[opt[0]] = opt[1]

    style = _detect_user_style(keybindings, options)

    return TmuxConfig(
        path=str(config_path),
        keybindings=keybindings,
        raw_options=options,
        style=style,
    )


def generate_default_config() -> str:
    """Generate a sensible default tmux configuration."""
    return """\
# tmux-learn generated config
# Sensible defaults for a good tmux experience

# Use Ctrl-a as prefix (easier than Ctrl-b)
set-option -g prefix C-a
unbind C-b
bind C-a send-prefix

# Start window numbering at 1
set -g base-index 1
setw -g pane-base-index 1

# Enable mouse support
set -g mouse on

# Vim-style pane navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Easier splits (and open in current path)
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Reload config
bind r source-file ~/.tmux.conf \\; display "Config reloaded!"

# Better colors
set -g default-terminal "screen-256color"

# Faster escape time
set -sg escape-time 10

# Increase history
set -g history-limit 10000
"""

"""
Parse tmux keybind notation to human-readable display format.
"""

import sys

# Detect if running on macOS
IS_MACOS = sys.platform == "darwin"


def parse_keybind(keybind: str) -> str:
    """
    Convert tmux keybind notation to display format.

    Examples (Linux/Ubuntu):
        M-H -> Alt + H
        C-a -> Ctrl + A
        M-{ -> Alt + {
        Space -> Space

    Examples (macOS):
        M-H -> Option + H
        C-a -> Ctrl + A
        M-{ -> Option + {
        Space -> Space
    """
    result = keybind.strip()

    # Handle modifier prefixes
    parts = []

    # Check for Meta/Alt prefix
    # On macOS, Alt is labeled "Option"
    if result.startswith("M-"):
        parts.append("Option" if IS_MACOS else "Alt")
        result = result[2:]
    # Check for Ctrl prefix
    elif result.startswith("C-"):
        parts.append("Ctrl")
        result = result[2:]
    # Check for Shift prefix (S-)
    elif result.startswith("S-"):
        parts.append("Shift")
        result = result[2:]

    # Handle special key names
    special_keys = {
        "Space": "Space",
        "Enter": "Enter",
        "Tab": "Tab",
        "BSpace": "Backspace",
        "Escape": "Escape",
        "Up": "Up",
        "Down": "Down",
        "Left": "Left",
        "Right": "Right",
        "Home": "Home",
        "End": "End",
        "PageUp": "Page Up",
        "PageDown": "Page Down",
        "F1": "F1", "F2": "F2", "F3": "F3", "F4": "F4",
        "F5": "F5", "F6": "F6", "F7": "F7", "F8": "F8",
        "F9": "F9", "F10": "F10", "F11": "F11", "F12": "F12",
    }

    if result in special_keys:
        parts.append(special_keys[result])
    else:
        # For single characters, display as-is (preserve case)
        parts.append(result)

    return " + ".join(parts)


def get_expected_key(keybind: str) -> tuple[set[str], str]:
    """
    Get the expected modifiers and key for matching.

    Returns:
        (modifiers_set, key) where modifiers_set contains 'alt', 'ctrl', 'shift'
        and key is the lowercase key name.

    Note: In tmux notation:
        M-h = Alt + h (lowercase)
        M-H = Alt + Shift + H (uppercase, requires shift)
        M-{ = Alt + Shift + [ (shifted character)
    """
    result = keybind.strip()
    modifiers = set()

    # Check for Meta/Alt prefix
    if result.startswith("M-"):
        modifiers.add("alt")
        result = result[2:]
    # Check for Ctrl prefix
    elif result.startswith("C-"):
        modifiers.add("ctrl")
        result = result[2:]
    # Check for Shift prefix
    elif result.startswith("S-"):
        modifiers.add("shift")
        result = result[2:]

    # Map special key names to pynput key names
    key_map = {
        "Space": "space",
        "Enter": "enter",
        "Tab": "tab",
        "BSpace": "backspace",
        "Escape": "escape",
        "Up": "up",
        "Down": "down",
        "Left": "left",
        "Right": "right",
    }

    if result in key_map:
        return (modifiers, key_map[result])

    # For single characters, check if shift is needed
    # Uppercase letters require shift
    if len(result) == 1 and result.isupper():
        modifiers.add("shift")
        return (modifiers, result.lower())

    # Shifted symbols - these require shift but come through as the symbol
    shifted_symbols = {
        "{": ("[", True),   # Shift+[ = {
        "}": ("]", True),   # Shift+] = }
        "<": (",", True),   # Shift+, = <
        ">": (".", True),   # Shift+. = >
        "|": ("\\", True),  # Shift+\ = |
        "!": ("1", True),
        "@": ("2", True),
        "#": ("3", True),
        "$": ("4", True),
        "%": ("5", True),
        "^": ("6", True),
        "&": ("7", True),
        "*": ("8", True),
        "(": ("9", True),
        ")": ("0", True),
        "_": ("-", True),
        "+": ("=", True),
        "~": ("`", True),
        ":": (";", True),
        '"': ("'", True),
        "?": ("/", True),
    }

    if result in shifted_symbols:
        base_key, needs_shift = shifted_symbols[result]
        if needs_shift:
            modifiers.add("shift")
        # Return the symbol itself - pynput gives us the actual character typed
        return (modifiers, result.lower())

    return (modifiers, result.lower())


if __name__ == "__main__":
    # Test cases
    test_cases = [
        "M-H", "M-h", "M-J", "M-K", "M-L",
        "C-a", "C-b",
        "M-{", "M-}", "M-<", "M->",
        "Space", "Enter", "Tab",
        "r", "x", "|", "-",
    ]

    for kb in test_cases:
        display = parse_keybind(kb)
        modifiers, key = get_expected_key(kb)
        print(f"{kb:10} -> {display:20} (mods={modifiers}, key={key})")

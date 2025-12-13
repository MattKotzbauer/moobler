#!/usr/bin/env python3
"""
Keybind Practice Overlay - CLI entry point.

Usage:
    python3 main.py --sequence '[{"key": "M-H", "description": "Resize left"}, ...]'
    python3 main.py --keybind "M-H"
    python3 main.py --keybind "M-h" --debug  # Enable debug output

Exit codes:
    0 = completed all keybinds
    1 = user pressed escape
    2 = error
"""

import argparse
import json
import sys

from PySide6.QtWidgets import QApplication

from .window import OverlayWindow
from .sequence import SequenceController, KeybindStep


def main():
    parser = argparse.ArgumentParser(description="Keybind practice overlay")
    parser.add_argument(
        "--sequence",
        type=str,
        help='JSON array of keybinds: [{"key": "M-H", "description": "..."}, ...]',
    )
    parser.add_argument(
        "--keybind",
        type=str,
        help="Single keybind to practice (e.g., M-H)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output to stderr",
    )

    args = parser.parse_args()

    # Build steps list
    steps: list[KeybindStep] = []

    if args.sequence:
        try:
            data = json.loads(args.sequence)
            for item in data:
                if isinstance(item, dict):
                    keybind = item.get("key") or item.get("keybind", "")
                    description = item.get("description", "")
                    if keybind:
                        steps.append(KeybindStep(keybind=keybind, description=description))
                elif isinstance(item, str):
                    steps.append(KeybindStep(keybind=item, description=""))
        except json.JSONDecodeError as e:
            print(f"Error parsing sequence JSON: {e}", file=sys.stderr)
            return 2
    elif args.keybind:
        steps.append(KeybindStep(keybind=args.keybind, description=""))
    else:
        print("Error: Must provide --sequence or --keybind", file=sys.stderr)
        return 2

    if not steps:
        print("Error: No valid keybinds provided", file=sys.stderr)
        return 2

    # Create Qt application
    app = QApplication(sys.argv)

    # Create overlay window
    window = OverlayWindow()
    window.show()

    # Create sequence controller
    controller = SequenceController(steps, window, debug=args.debug)
    controller.start()

    # Run event loop
    app.exec()

    # Return exit code based on result
    if controller.completed:
        return 0
    elif controller.escaped:
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())

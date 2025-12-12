"""Entry point for tmux-learn."""

import sys

from .ui.app import TmuxLearnApp


def main() -> int:
    """Run the tmux-learn application."""
    app = TmuxLearnApp()
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

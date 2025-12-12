"""Main Textual application."""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from .screens.home import HomeScreen
from .screens.config_view import ConfigViewScreen
from .screens.discover import DiscoverScreen
from .screens.sandbox import SandboxScreen


class TmuxLearnApp(App):
    """AI-powered tmux tutor application."""

    TITLE = "tmux-learn"
    SUB_TITLE = "Learn new tmux controls with AI"

    CSS = """
    Screen {
        background: $surface;
    }

    #main-content {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    .title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    .subtitle {
        color: $text-muted;
        margin-bottom: 2;
    }

    .card {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        background: $surface-darken-1;
    }

    .card:hover {
        background: $surface-lighten-1;
    }

    .keybind {
        color: $success;
        text-style: bold;
    }

    .command {
        color: $warning;
    }

    .hint {
        color: $text-muted;
        text-style: italic;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("h", "go_home", "Home", show=True),
        Binding("c", "view_config", "Config", show=True),
        Binding("d", "discover", "Discover", show=True),
        Binding("s", "sandbox", "Sandbox", show=True),
        Binding("?", "help", "Help", show=True),
    ]

    SCREENS = {
        "home": HomeScreen,
        "config": ConfigViewScreen,
        "discover": DiscoverScreen,
        "sandbox": SandboxScreen,
    }

    def compose(self) -> ComposeResult:
        """Compose the app layout."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.push_screen("home")

    def action_go_home(self) -> None:
        """Navigate to home screen."""
        self.switch_screen("home")

    def action_view_config(self) -> None:
        """Navigate to config view screen."""
        self.switch_screen("config")

    def action_discover(self) -> None:
        """Navigate to discover screen."""
        self.switch_screen("discover")

    def action_sandbox(self) -> None:
        """Navigate to sandbox screen."""
        self.switch_screen("sandbox")

    def action_help(self) -> None:
        """Show help."""
        self.notify(
            "h=Home, c=Config, d=Discover, s=Sandbox, q=Quit",
            title="Keyboard shortcuts",
        )

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

    /* Vim-style focus indicators */
    *:focus {
        border: solid $success;
    }

    Button:focus {
        background: $primary-darken-1;
    }

    ListView > ListItem.--highlight {
        background: $primary-darken-2;
    }
    """

    BINDINGS = [
        # Screen navigation (number keys)
        Binding("1", "go_home", "1:Home", show=True),
        Binding("2", "view_config", "2:Config", show=True),
        Binding("3", "discover", "3:Discover", show=True),
        Binding("4", "sandbox", "4:Sandbox", show=True),
        # Vim navigation
        Binding("j", "focus_next", "j:Down", show=True),
        Binding("k", "focus_previous", "k:Up", show=True),
        Binding("h", "focus_left", "h:Left", show=False),
        Binding("l", "focus_right", "l:Right", show=False),
        # Widget jumping
        Binding("w", "focus_next_widget", "w:Next", show=False),
        Binding("b", "focus_prev_widget", "b:Prev", show=False),
        # Actions
        Binding("enter", "select", "Select", show=False),
        Binding("space", "select", "Select", show=False),
        Binding("o", "select", "o:Open", show=False),
        # Top/bottom
        Binding("g", "go_top", "g:Top", show=False),
        Binding("G", "go_bottom", "G:Bottom", show=False),
        # Tabs (for tabbed content)
        Binding("H", "prev_tab", "H:PrevTab", show=False),
        Binding("L", "next_tab", "L:NextTab", show=False),
        # Quit/help
        Binding("q", "quit", "q:Quit", show=True),
        Binding("?", "help", "?:Help", show=True),
        # Escape to go back
        Binding("escape", "go_back", "Esc:Back", show=False),
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

    def action_go_back(self) -> None:
        """Go back to previous screen or home."""
        if len(self.screen_stack) > 1:
            self.pop_screen()
        else:
            self.switch_screen("home")

    def action_focus_next(self) -> None:
        """Move focus to next focusable widget (vim j)."""
        self.screen.focus_next()

    def action_focus_previous(self) -> None:
        """Move focus to previous focusable widget (vim k)."""
        self.screen.focus_previous()

    def action_focus_left(self) -> None:
        """Move focus left."""
        # Try to find a widget to the left
        self.screen.focus_previous()

    def action_focus_right(self) -> None:
        """Move focus right."""
        # Try to find a widget to the right
        self.screen.focus_next()

    def action_focus_next_widget(self) -> None:
        """Jump to next widget section (vim w)."""
        self.screen.focus_next()

    def action_focus_prev_widget(self) -> None:
        """Jump to previous widget section (vim b)."""
        self.screen.focus_previous()

    def action_select(self) -> None:
        """Activate the focused widget (like pressing enter)."""
        focused = self.screen.focused
        if focused is not None:
            # Simulate a click on the focused widget
            focused.post_message(focused.Pressed(focused) if hasattr(focused, "Pressed") else None)

    def action_go_top(self) -> None:
        """Go to first focusable widget (vim g/gg)."""
        focusables = list(self.screen.query("*:focusable"))
        if focusables:
            focusables[0].focus()

    def action_go_bottom(self) -> None:
        """Go to last focusable widget (vim G)."""
        focusables = list(self.screen.query("*:focusable"))
        if focusables:
            focusables[-1].focus()

    def action_prev_tab(self) -> None:
        """Go to previous tab (vim H)."""
        from textual.widgets import TabbedContent
        try:
            tabs = self.screen.query_one(TabbedContent)
            tabs.action_previous_tab()
        except Exception:
            pass

    def action_next_tab(self) -> None:
        """Go to next tab (vim L)."""
        from textual.widgets import TabbedContent
        try:
            tabs = self.screen.query_one(TabbedContent)
            tabs.action_next_tab()
        except Exception:
            pass

    def action_help(self) -> None:
        """Show help."""
        self.notify(
            "Navigation: j/k=Down/Up, h/l=Left/Right, w/b=Next/Prev widget\n"
            "Screens: 1=Home, 2=Config, 3=Discover, 4=Sandbox\n"
            "Actions: Enter/Space/o=Select, g/G=Top/Bottom, H/L=Prev/Next Tab\n"
            "Other: Esc=Back, q=Quit",
            title="Vim Keybindings",
            timeout=10,
        )

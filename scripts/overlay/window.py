"""
Transparent overlay window using PySide6.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QFont, QColor, QPalette, QKeyEvent


class OverlaySignals(QObject):
    """Signals for thread-safe GUI updates."""
    update_keybind = Signal(str, str, int, int)  # keybind, description, current, total
    flash_success = Signal()
    flash_wrong = Signal()
    close_window = Signal()
    key_pressed = Signal(str, list)  # key, modifiers (as list since Qt doesn't support set)


class OverlayWindow(QMainWindow):
    """Translucent fullscreen overlay for keybind practice."""

    def __init__(self):
        super().__init__()

        self.signals = OverlaySignals()
        self.signals.update_keybind.connect(self._update_display)
        self.signals.flash_success.connect(self._flash_success)
        self.signals.flash_wrong.connect(self._flash_wrong)
        self.signals.close_window.connect(self.close)

        self._setup_window()
        self._setup_ui()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events directly in Qt."""
        key = event.key()
        modifiers = event.modifiers()

        # Check for Escape - always allow exit
        if key == Qt.Key.Key_Escape:
            self.signals.key_pressed.emit("escape", [])
            return

        # Build modifier set
        mods = set()
        if modifiers & Qt.KeyboardModifier.AltModifier:
            mods.add("alt")
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            mods.add("ctrl")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            mods.add("shift")

        # Get key name
        key_text = event.text().lower() if event.text() else ""

        # Map special keys
        special_keys = {
            Qt.Key.Key_Space: "space",
            Qt.Key.Key_Return: "enter",
            Qt.Key.Key_Enter: "enter",
            Qt.Key.Key_Tab: "tab",
            Qt.Key.Key_Backspace: "backspace",
            Qt.Key.Key_Up: "up",
            Qt.Key.Key_Down: "down",
            Qt.Key.Key_Left: "left",
            Qt.Key.Key_Right: "right",
        }

        if key in special_keys:
            key_text = special_keys[key]
        elif not key_text:
            # Try to get from key code for letters
            if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
                key_text = chr(key).lower()

        if key_text:
            self.signals.key_pressed.emit(key_text, list(mods))

    def _setup_window(self):
        """Configure window for transparent fullscreen overlay."""
        # Window flags for transparent overlay
        # Note: NOT using X11BypassWindowManagerHint so we can receive keyboard focus
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |      # No window decorations
            Qt.WindowType.WindowStaysOnTopHint |     # Always on top
            Qt.WindowType.Tool                       # Don't show in taskbar
        )

        # Enable transparency
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Fullscreen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        # Make sure we can receive keyboard input
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def showEvent(self, event):
        """Ensure we grab keyboard focus when shown."""
        super().showEvent(event)
        self.activateWindow()
        self.raise_()
        self.setFocus()

    def _setup_ui(self):
        """Create the overlay UI."""
        # Central widget with semi-transparent background
        central = QWidget()
        central.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        self.setCentralWidget(central)

        # Layout
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Keybind display (large, stylized text)
        self.keybind_label = QLabel("Alt + H")
        self.keybind_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.keybind_label.setStyleSheet("""
            QLabel {
                color: #00ffff;
                font-size: 96px;
                font-weight: bold;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                padding: 40px 80px;
                border: 4px solid #00ffff;
                border-radius: 20px;
                background-color: rgba(0, 255, 255, 30);
            }
        """)
        layout.addWidget(self.keybind_label)

        # Spacer
        layout.addSpacing(30)

        # Progress indicator
        self.progress_label = QLabel("[1 / 4]")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
            }
        """)
        layout.addWidget(self.progress_label)

        # Description
        self.description_label = QLabel("Resize pane left")
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.description_label.setStyleSheet("""
            QLabel {
                color: #aaaaaa;
                font-size: 20px;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
            }
        """)
        layout.addWidget(self.description_label)

        # Spacer
        layout.addSpacing(60)

        # Escape hint
        self.hint_label = QLabel("Press Escape to exit")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
            }
        """)
        layout.addWidget(self.hint_label)

    def _update_display(self, keybind: str, description: str, current: int, total: int):
        """Update the displayed keybind and progress."""
        self.keybind_label.setText(keybind)
        self.progress_label.setText(f"[{current} / {total}]")
        self.description_label.setText(description)

        # Reset to default style (cyan)
        self.keybind_label.setStyleSheet("""
            QLabel {
                color: #00ffff;
                font-size: 96px;
                font-weight: bold;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                padding: 40px 80px;
                border: 4px solid #00ffff;
                border-radius: 20px;
                background-color: rgba(0, 255, 255, 30);
            }
        """)

    def _flash_success(self):
        """Flash green to indicate correct key."""
        self.keybind_label.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 96px;
                font-weight: bold;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                padding: 40px 80px;
                border: 4px solid #00ff00;
                border-radius: 20px;
                background-color: rgba(0, 255, 0, 50);
            }
        """)

    def _flash_wrong(self):
        """Flash red to indicate wrong key."""
        self.keybind_label.setStyleSheet("""
            QLabel {
                color: #ff4444;
                font-size: 96px;
                font-weight: bold;
                font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
                padding: 40px 80px;
                border: 4px solid #ff4444;
                border-radius: 20px;
                background-color: rgba(255, 0, 0, 50);
            }
        """)

    # Thread-safe methods to call from other threads
    def update_keybind(self, keybind: str, description: str, current: int, total: int):
        """Thread-safe keybind update."""
        self.signals.update_keybind.emit(keybind, description, current, total)

    def flash_success(self):
        """Thread-safe success flash."""
        self.signals.flash_success.emit()

    def flash_wrong(self):
        """Thread-safe wrong flash."""
        self.signals.flash_wrong.emit()

    def close_overlay(self):
        """Thread-safe close."""
        self.signals.close_window.emit()

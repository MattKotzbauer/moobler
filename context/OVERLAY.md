# Keybind Practice Overlay

## Overview

A translucent fullscreen overlay that guides users through a sequence of keybinds during sandbox practice. The overlay:
1. Shows the current keybind to press (e.g., "Alt + L") in large, stylized text
2. Locks all other input until the correct key is pressed
3. Progresses through a sequence of keybinds
4. Has an emergency escape (Escape key)

## Architecture

```
User enters Sandbox
    │
    ├── Claude generates practice sequence from keybind group
    │   e.g., ["M-H", "M-J", "M-K", "M-L"] for resize panes
    │
    └── Bun spawns: python3 scripts/overlay/main.py --sequence '["Alt+H","Alt+J","Alt+K","Alt+L"]'
                        │
                        ├── For each keybind in sequence:
                        │   ├── Show translucent overlay with keybind text
                        │   ├── Grab keyboard input
                        │   ├── Wait for correct key OR escape
                        │   └── Flash green on success, advance
                        │
                        └── Exit with status:
                            0 = completed all
                            1 = user escaped
                            2 = error
```

## Technology Stack

### Ubuntu/Linux
- **Window**: PySide6 (Qt) with frameless transparent window
- **Keyboard**: Qt's native keyPressEvent for keyboard capture
- **Text**: Qt's QLabel with custom font styling
- **Display**: Shows "Alt" for Meta modifier keys

### macOS
- **Window**: PySide6 (Qt) with frameless transparent window + macOS-specific attributes
- **Keyboard**: Qt's native keyPressEvent (Option key maps to AltModifier)
- **Text**: Qt's QLabel with custom font styling
- **Display**: Shows "Option" for Meta modifier keys (macOS convention)
- **Requirements**: May need to grant accessibility permissions in System Preferences → Security & Privacy → Privacy → Accessibility

## File Structure

```
scripts/
└── overlay/
    ├── __init__.py
    ├── main.py              # CLI entry point
    ├── window.py            # PySide6 transparent overlay window
    ├── keyboard_listener.py # pynput keyboard capture
    ├── sequence.py          # Multi-step sequence controller
    ├── keybind_parser.py    # Parse "M-H" to displayable "Alt + H"
    └── requirements.txt
```

## Key Components

### 1. Transparent Window (window.py)
```python
# Key Qt flags for transparency
self.setWindowFlags(
    Qt.FramelessWindowHint |      # No window decorations
    Qt.WindowStaysOnTopHint |     # Always on top
    Qt.Tool |                     # Don't show in taskbar
    Qt.X11BypassWindowManagerHint # Bypass WM on X11
)
self.setAttribute(Qt.WA_TranslucentBackground)
self.setAttribute(Qt.WA_ShowWithoutActivating)
```

### 2. Keyboard Capture (keyboard_listener.py)
```python
from pynput import keyboard

# Global listener that captures ALL keyboard input
listener = keyboard.Listener(
    on_press=on_press,
    suppress=True  # Suppress keys from reaching other apps
)
```

### 3. Sequence Controller (sequence.py)
- Receives list of keybinds to practice
- Tracks current position in sequence
- Signals window to update display
- Handles success/escape events

### 4. Keybind Parser (keybind_parser.py)
Converts tmux notation to display format:
- `M-H` → `Alt + H`
- `C-a` → `Ctrl + A`
- `Space` → `Space`
- `M-{` → `Alt + {`

## Visual Design

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              (translucent dark overlay)                 │
│                                                         │
│                                                         │
│                    ╔═══════════════╗                    │
│                    ║   Alt + H     ║                    │
│                    ╚═══════════════╝                    │
│                                                         │
│                   [1 / 4] Resize Left                   │
│                                                         │
│                  Press Escape to exit                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

- Background: rgba(0, 0, 0, 0.7) - dark translucent
- Keybind text: Large (72pt+), white/cyan, maybe with glow effect
- Progress: Smaller text showing position in sequence
- Hint: Small gray text at bottom

## Integration with Sandbox

### Current Sandbox Flow
1. User selects keybind group in Discover
2. Goes to Sandbox screen
3. Presses 's' to start
4. Docker container launches with tmux

### New Flow with Overlay
1. User selects keybind group in Discover
2. Goes to Sandbox screen
3. Presses 's' to start
4. Docker container launches with tmux
5. **Overlay spawns on top with first keybind**
6. **User practices each keybind in sequence**
7. **Overlay closes, user has free practice time**

### Bun Integration
```typescript
// In sandbox launch flow
const sequence = keybindsToTry.keybinds.map(kb => ({
  key: kb.keybind,
  description: kb.description
}));

const overlay = Bun.spawn([
  "python3",
  "scripts/overlay/main.py",
  "--sequence", JSON.stringify(sequence)
], { stdin: "inherit", stdout: "inherit", stderr: "inherit" });

const exitCode = await overlay.exited;
// 0 = success, 1 = escaped, 2 = error
```

## Dependencies

```txt
# scripts/overlay/requirements.txt
PySide6>=6.5.0
pynput>=1.7.6
```

Install with:
```bash
pip install -r scripts/overlay/requirements.txt
# or
uv pip install -r scripts/overlay/requirements.txt
```

## Platform-Specific Notes

### Ubuntu/X11
- Works natively with X11
- May need `$DISPLAY` environment variable set
- Uses Qt's native keyboard handling

### Ubuntu/Wayland
- Limited support via Xwayland
- May only capture from X11 apps
- Consider forcing X11 session for full functionality

### macOS
- **Supported** - Uses PySide6 with macOS-specific window attributes
- Option key (⌥) is used instead of Alt and displays as "Option"
- May need to grant accessibility permissions:
  - System Preferences → Security & Privacy → Privacy → Accessibility
  - Add Terminal or the running application to allowed list
- Window uses `WA_MacAlwaysShowToolWindow` attribute for proper keyboard focus
- Works with both Intel and Apple Silicon Macs

## Testing

```bash
# Test overlay directly
python3 scripts/overlay/main.py --sequence '["Alt+H", "Alt+L"]'

# Test with single keybind
python3 scripts/overlay/main.py --keybind "Alt+H"

# Test escape functionality
# Press Escape during overlay - should exit with code 1
```

## Future Enhancements

1. **Sound effects**: Beep on correct key, different sound on wrong key
2. **Visual feedback**: Flash green on success, red on wrong key
3. **Timing**: Show how long each keypress took
4. **Statistics**: Track accuracy over multiple sessions
5. **Adaptive difficulty**: Faster timeouts as user improves

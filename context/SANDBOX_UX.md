# Sandbox UX Design

## Problem
Current flow requires user to manually:
1. See the `docker exec -it tmux-sandbox tmux attach` command
2. Open a new terminal/pane
3. Copy-paste and run the command
4. Practice the keybind
5. Exit and return to the app

This is especially awkward when:
- Running inside tmux (tmux-in-tmux nesting)
- User doesn't know how to split tmux panes
- Context switching breaks flow

## User's Environment
- Terminal: Kitty
- Often runs inside tmux
- Ubuntu Linux

## Proposed Solution: Auto-detect and Launch

### Detection Logic
```python
import os
import shutil

def get_terminal_context():
    """Detect what terminal environment we're in."""
    if os.environ.get("TMUX"):
        return "tmux"
    elif os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    elif os.environ.get("TERM_PROGRAM") == "vscode":
        return "vscode"
    elif shutil.which("kitty"):
        return "kitty_available"
    elif shutil.which("gnome-terminal"):
        return "gnome"
    else:
        return "unknown"
```

### Launch Strategies

#### 1. Inside tmux → Split pane
```python
def launch_in_tmux_pane(docker_cmd):
    """Split current tmux and run sandbox."""
    # -h = horizontal split (side by side)
    # After docker exits, 'read' keeps pane open so user can see output
    cmd = f'tmux split-window -h "{docker_cmd}; echo Press enter to close; read"'
    os.system(cmd)
```

Pros:
- Seamless, stays in same terminal
- User can see app and sandbox side by side
- Easy to switch between them

Cons:
- Tmux-in-tmux can be confusing
- Prefix key might conflict

#### 2. Kitty → New OS window
```python
def launch_in_kitty(docker_cmd):
    """Open new Kitty window with sandbox."""
    # --hold keeps window open after command exits
    cmd = f'kitty --hold --title "tmux-learn sandbox" {docker_cmd}'
    os.system(cmd)
```

Pros:
- Clean separation
- No tmux-in-tmux issue
- Works when not in tmux

Cons:
- Window might appear behind current one
- Need to manually switch windows

#### 3. Generic → xterm/gnome-terminal fallback
```python
def launch_in_xterm(docker_cmd):
    """Fallback to xterm."""
    cmd = f'xterm -hold -e "{docker_cmd}"'
    os.system(cmd)
```

### Recommended Implementation

```python
# In src/ui/screens/sandbox.py

import os
import shutil
import subprocess

def launch_sandbox_terminal(self):
    """Launch sandbox in appropriate terminal."""
    docker_cmd = self._container_manager.get_attach_command()

    context = self._get_terminal_context()

    if context == "tmux":
        # Inside tmux: split pane horizontally
        subprocess.Popen([
            "tmux", "split-window", "-h",
            f'{docker_cmd}; echo ""; echo "Press Enter to close..."; read'
        ])
        self._log("Opened sandbox in new tmux pane (to the right)")
        self._log("Practice your keybind, then exit tmux to return here")

    elif context in ("kitty", "kitty_available"):
        # Kitty: open new window
        subprocess.Popen([
            "kitty", "--hold", "--title", "tmux-learn sandbox",
            "sh", "-c", docker_cmd
        ])
        self._log("Opened sandbox in new Kitty window")
        self._log("Switch to that window to practice")

    else:
        # Fallback: try xterm or just show instructions
        if shutil.which("xterm"):
            subprocess.Popen(["xterm", "-hold", "-e", docker_cmd])
            self._log("Opened sandbox in xterm window")
        else:
            self._log("Could not auto-open terminal.")
            self._log(f"Please run manually: {docker_cmd}")

def _get_terminal_context(self):
    if os.environ.get("TMUX"):
        return "tmux"
    elif os.environ.get("KITTY_WINDOW_ID") or shutil.which("kitty"):
        return "kitty"
    else:
        return "unknown"
```

### UI Flow After Implementation

1. User selects keybind → presses `t`
2. Goes to Sandbox screen, keybind displayed
3. User presses `s` to start
4. Container starts
5. **Automatically**: New pane/window opens with sandbox attached
6. User practices keybind with challenge displayed
7. User exits sandbox (`exit` or `Ctrl+d`)
8. Returns to app, prompted: "Did you like it? [Keep] [Discard]"

### Challenge Display in Sandbox

The sandbox entrypoint could display the challenge:
```bash
# In docker/entrypoint.sh, if challenge info is mounted:
if [ -f /tmp/challenge.txt ]; then
    echo "=== CHALLENGE ==="
    cat /tmp/challenge.txt
    echo "================="
fi
```

Or display in the TUI before launching, so user knows what to do.

## Alternative: Embedded Terminal

Could use a library like `pyte` or `terminado` to embed a terminal in the Textual UI. However:
- Complex to implement
- May have rendering issues
- Textual not designed for this

**Recommendation**: Stick with external terminal approach, it's simpler and more reliable.

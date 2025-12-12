#!/bin/bash
set -e

# Create default tmux.conf if none exists
if [ ! -f "$HOME/.tmux.conf" ]; then
    cat > "$HOME/.tmux.conf" << 'EOF'
# tmux-learn sandbox config
# This config is for learning - feel free to experiment!

# Enable mouse
set -g mouse on

# Start windows and panes at 1
set -g base-index 1
setw -g pane-base-index 1

# Better colors
set -g default-terminal "screen-256color"

# Status bar
set -g status-style 'bg=colour235 fg=colour136'
set -g status-left '[#S] '
set -g status-right '%H:%M '

# Highlight active pane
set -g pane-active-border-style 'fg=colour136'

# Display message when config is loaded
run-shell 'tmux display-message "Sandbox ready! Practice your keybindings."'
EOF
fi

# If user config was mounted, append it
if [ -f "/tmp/user-tmux.conf" ]; then
    echo "" >> "$HOME/.tmux.conf"
    echo "# User config (from your system)" >> "$HOME/.tmux.conf"
    cat "/tmp/user-tmux.conf" >> "$HOME/.tmux.conf"
fi

# If test bindings were provided, append them
if [ -f "/tmp/test-bindings.conf" ]; then
    echo "" >> "$HOME/.tmux.conf"
    echo "# Test bindings (new keybinds to try)" >> "$HOME/.tmux.conf"
    cat "/tmp/test-bindings.conf" >> "$HOME/.tmux.conf"
fi

# Start with a multi-pane layout for practice
setup_practice_layout() {
    tmux new-session -d -s learn -c "$HOME/practice"

    # Create a 2x2 grid of panes
    tmux split-window -h -c "$HOME/practice"
    tmux split-window -v -c "$HOME/practice"
    tmux select-pane -t 0
    tmux split-window -v -c "$HOME/practice"

    # Put different content in each pane
    tmux send-keys -t 0 'cat readme.txt' C-m
    tmux send-keys -t 1 'ls -la' C-m
    tmux send-keys -t 2 'cat file1.txt' C-m
    tmux send-keys -t 3 'tree' C-m

    # Select first pane
    tmux select-pane -t 0
}

# Execute the command or start default session
if [ "$1" = "tmux" ] && [ "$2" = "new-session" ]; then
    setup_practice_layout
    exec tmux attach-session -t learn
else
    exec "$@"
fi

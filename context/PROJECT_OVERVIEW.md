# tmux-learn: AI-Powered Tmux Tutor

## Vision
An interactive CLI/TUI app that teaches users new tmux keybindings through:
1. AI-powered suggestions based on their existing config
2. Safe containerized sandbox to try new keybindings
3. Mini-challenges to practice and learn
4. One-click integration of approved keybindings into their real config

## Tech Stack
- **Language**: Python 3.11+
- **TUI**: Textual (responsive, modern terminal UI)
- **AI**: Claude API (Anthropic) for suggestions & challenge generation
- **Containers**: Docker for isolated tmux sandbox
- **Storage**: SQLite for progress tracking
- **Config**: Pydantic models

## Current State (as of session end)

### Working
- Project structure complete
- Textual TUI with 4 screens (Home, Config, Discover, Sandbox)
- Vim-style navigation (j/k/h/l) throughout
- Config parser that detects user's style (vim keys, Meta preference, etc.)
- Curated tips database (~20 tips)
- Basic suggestion filtering based on user's style
- Docker sandbox infrastructure (container manager, Dockerfile)
- Keybind cards with Try/Add/Details actions

### Needs Work
1. **Claude AI Integration** - Infrastructure exists but not wired to UI
2. **Sandbox UX** - Currently requires manual docker exec in separate terminal
3. **Challenge System** - Types defined but not integrated into UI
4. **Config Merger** - Code exists but not connected to "Add" button

## Key User Flows

### Discover Flow
1. User opens app → Home screen
2. Press `3` → Discover screen
3. `h`/`l` to switch between categories (left) and suggestions (right)
4. `j`/`k` to navigate suggestions
5. `t` to try in sandbox, `a` to add to config, `d` for details

### Sandbox Flow (current - needs improvement)
1. Select keybind in Discover → press `t`
2. Goes to Sandbox screen with keybind info displayed
3. Press `s` to start Docker container
4. **Problem**: User must manually open another terminal and run docker exec
5. Practice keybind, exit, press `x` to stop container

### Desired Sandbox Flow
1. Press `t` on a keybind
2. App automatically opens sandbox in new pane/window/terminal
3. User practices with guided challenge
4. Exit returns to app with "Keep it?" prompt

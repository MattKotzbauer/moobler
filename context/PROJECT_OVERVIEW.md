# moobler: AI-Powered Tmux Tutor

## Vision
An interactive TUI app that teaches users new tmux keybindings through:
1. AI-powered suggestions based on their existing config and popular GitHub dotfiles
2. Safe containerized sandbox to try new keybindings (with user's real config loaded)
3. Grouped keybindings for cohesive learning (e.g., all resize directions together)
4. One-click integration of approved keybindings into their real config

## Tech Stack
- **Language**: Python 3.11+
- **TUI**: Textual (responsive, modern terminal UI with vim-style navigation)
- **AI**: Claude API (Anthropic) for smart suggestions & challenge generation
- **Containers**: Docker for isolated tmux sandbox
- **Storage**: SQLite for progress tracking (infrastructure ready)
- **Config**: Pydantic models for parsing and validation

## Current State

### Fully Working
- Textual TUI with 4 screens (Home, Config, Discover, Sandbox)
- Vim-style navigation (j/k/h/l) throughout the app
- Config parser that detects user's style (vim keys, Meta preference, etc.)
- **Smart AI suggestions**: Claude reads user config + scrapes GitHub dotfiles to suggest grouped keybindings
- **Docker sandbox**: Launches in fullscreen Kitty terminal with user's real config + test bindings
- **Pre-warmed containers**: First sandbox launch is instant (container pre-started on app launch)
- Keybind cards with Try/Add/Details actions and h/l navigation within cards
- Config merger for adding keybindings to user's ~/.tmux.conf with automatic backups
- Challenge generation (AI creates practice objectives for keybindings)

### Known Limitations
- Pre-warm only works for first sandbox launch per session (subsequent launches use cold start)
- Progress tracking UI not implemented (database infrastructure exists)
- Challenge validation not automated (user self-validates)

---

## Project Structure

```
tmux_learn/
├── pyproject.toml          # Package config, dependencies, "moobler" command entry point
├── base_prompt.txt         # Original project requirements/prompt
├── context/
│   └── PROJECT_OVERVIEW.md # This file
├── data/
│   └── curated_tips.json   # Hand-curated tmux tips database (~20 tips)
├── docker/
│   ├── Dockerfile          # Sandbox container image (Ubuntu + tmux)
│   └── entrypoint.sh       # Container startup script
└── src/
    ├── main.py             # Entry point - runs TmuxLearnApp
    ├── ai/                 # AI/Claude integration
    ├── challenges/         # Challenge system (types, engine)
    ├── config/             # tmux.conf parsing and merging
    ├── container/          # Docker sandbox management
    ├── discovery/          # Keybinding discovery (GitHub scraping, curated tips)
    ├── storage/            # SQLite database for progress
    └── ui/                 # Textual TUI screens and widgets
```

---

## Directory & File Roles

### `/src/ui/` - User Interface (Textual TUI)

| File | Role | Main Implementation? |
|------|------|---------------------|
| `app.py` | Main application class, global keybindings, screen routing, container pre-warming | **YES** |
| `screens/home.py` | Welcome screen with moobler ASCII art, config status, navigation buttons | YES |
| `screens/discover.py` | Main discovery UI - category list, AI suggestions, keybind cards | **YES** |
| `screens/sandbox.py` | Docker sandbox launcher, challenge display, pre-warm integration | **YES** |
| `screens/config_view.py` | Display user's current tmux.conf with syntax highlighting | |
| `widgets/keybind_card.py` | Reusable card component for displaying keybind suggestions | YES |

### `/src/ai/` - Claude AI Integration

| File | Role | Main Implementation? |
|------|------|---------------------|
| `smart_suggester.py` | **Core AI logic**: Reads user config + GitHub data, asks Claude for grouped suggestions | **YES** |
| `client.py` | Low-level Claude API wrapper, challenge generation | YES |
| `suggester.py` | Legacy/simple suggester (style-based filtering without AI) | |
| `challenge_gen.py` | Challenge generation prompts and parsing | |

### `/src/config/` - tmux Configuration

| File | Role | Main Implementation? |
|------|------|---------------------|
| `parser.py` | Parse ~/.tmux.conf into structured data, detect user style | YES |
| `models.py` | Pydantic models: Keybinding, TmuxConfig, UserStyle, BindingMode | YES |
| `merger.py` | Add/remove keybindings to config with backups | YES |

### `/src/container/` - Docker Sandbox

| File | Role | Main Implementation? |
|------|------|---------------------|
| `manager.py` | Docker SDK wrapper: build image, start/stop containers, exec commands | YES |
| `tmux_bridge.py` | Send keys to tmux in container, capture pane contents | |

### `/src/discovery/` - Keybinding Discovery

| File | Role | Main Implementation? |
|------|------|---------------------|
| `github_scraper.py` | Scrape popular GitHub dotfiles for keybindings | YES |
| `curated.py` | Load and filter curated tips from JSON | |

### `/src/storage/` - Progress Tracking

| File | Role | Main Implementation? |
|------|------|---------------------|
| `database.py` | SQLite database setup and queries | |
| `progress.py` | Track learned keybindings, practice sessions | |

### `/src/challenges/` - Practice Challenges

| File | Role | Main Implementation? |
|------|------|---------------------|
| `types.py` | Challenge, ChallengeStep, ChallengeResult models | |
| `engine.py` | Challenge execution and validation logic | |

### `/docker/` - Container Configuration

| File | Role |
|------|------|
| `Dockerfile` | Ubuntu-based image with tmux, creates `learner` user |
| `entrypoint.sh` | Sets up tmux session on container start |

### `/data/` - Static Data

| File | Role |
|------|------|
| `curated_tips.json` | ~20 hand-picked tmux tips with categories and difficulty |

---

## Main Implementation Files (Priority Order)

These are the files that contain the core working functionality:

1. **`src/ui/app.py`** - Application shell, vim navigation, pre-warming
2. **`src/ui/screens/discover.py`** - Main discovery flow, AI integration point
3. **`src/ai/smart_suggester.py`** - Claude AI suggestions with GitHub data
4. **`src/ui/screens/sandbox.py`** - Docker sandbox with Kitty integration
5. **`src/config/parser.py`** - tmux.conf parsing and style detection
6. **`src/config/merger.py`** - Adding keybindings to user's config
7. **`src/discovery/github_scraper.py`** - Fetching popular configs from GitHub
8. **`src/container/manager.py`** - Docker container lifecycle
9. **`src/ui/widgets/keybind_card.py`** - Keybind display component
10. **`src/ui/screens/home.py`** - Home screen with moobler art

---

## Key User Flows

### Discovery Flow (Primary)
1. User starts `moobler` → Home screen with moobler ASCII art
2. Press `3` → Discover screen
3. Select category with `j`/`k` on left panel
4. Press `l` or click "Search Online" → AI fetches grouped suggestions
5. Navigate suggestions with `j`/`k`, within cards with `h`/`l`
6. Press `t` to try in sandbox, `a` to add to config

### Sandbox Flow
1. From Discover, press `t` on a keybind/group
2. Sandbox screen shows challenge info
3. Press `s` → Fullscreen Kitty window opens with:
   - User's existing ~/.tmux.conf loaded
   - New test keybindings appended
   - Challenge description displayed
4. Practice in isolated tmux environment
5. Exit tmux → returns to moobler
6. Press `a` in sandbox to add practiced keybinds to real config

### Config Addition Flow
1. From Sandbox, press "Apply to Config" button
2. ConfigMerger creates timestamped backup
3. Keybindings appended to ~/.tmux.conf
4. User runs `tmux source ~/.tmux.conf` to reload

---

## Environment Requirements

- Python 3.11+
- Docker (for sandbox)
- Kitty terminal (for fullscreen sandbox launch)
- ANTHROPIC_API_KEY environment variable (for AI features)

## Running

```bash
# Install
pip install -e .

# Run
moobler

# Or directly
python -m src.main
```

## Key Bindings (In App)

| Key | Action |
|-----|--------|
| `1-4` | Switch screens (Home/Config/Discover/Sandbox) |
| `j`/`k` | Navigate down/up |
| `h`/`l` | Navigate left/right, move between card actions |
| `Enter`/`o` | Select/activate |
| `t` | Try keybind in sandbox |
| `a` | Add keybind to config |
| `d` | Show keybind details |
| `g`/`G` | Go to top/bottom |
| `q` | Quit |
| `?` | Show help |
| `m` | Show moobler! |

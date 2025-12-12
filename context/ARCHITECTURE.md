# Architecture

## Directory Structure
```
tmux_learn/
├── src/
│   ├── main.py                 # Entry point
│   ├── config/                 # Config parsing
│   │   ├── models.py           # Pydantic: Keybinding, TmuxConfig, UserStyle
│   │   ├── parser.py           # Parse ~/.tmux.conf, detect style
│   │   └── merger.py           # Merge new keybinds into config
│   ├── discovery/              # Find new keybinds
│   │   ├── curated.py          # Built-in tips database (~20 tips)
│   │   └── github_scraper.py   # Scrape popular dotfiles (not used yet)
│   ├── ai/                     # Claude integration
│   │   ├── client.py           # Claude API wrapper
│   │   ├── suggester.py        # AI-powered suggestions
│   │   └── challenge_gen.py    # Generate learning challenges
│   ├── container/              # Docker sandbox
│   │   ├── manager.py          # Container lifecycle (start/stop)
│   │   └── tmux_bridge.py      # Communicate with tmux in container
│   ├── challenges/             # Learning system
│   │   ├── types.py            # Challenge, ChallengeType models
│   │   └── engine.py           # Run challenges, validate completion
│   ├── storage/                # Persistence
│   │   ├── database.py         # SQLite schema & queries
│   │   └── progress.py         # Track learning progress
│   └── ui/                     # Textual TUI
│       ├── app.py              # Main app, global keybindings
│       ├── screens/
│       │   ├── home.py         # Welcome, quick actions
│       │   ├── config_view.py  # View parsed config, style analysis
│       │   ├── discover.py     # Browse suggestions
│       │   └── sandbox.py      # Container sandbox UI
│       └── widgets/
│           └── keybind_card.py # Suggestion card with actions
├── docker/
│   ├── Dockerfile              # Ubuntu + tmux sandbox image
│   └── entrypoint.sh           # Sets up practice environment
├── data/
│   └── curated_tips.json       # Exportable tips (not primary source)
└── context/                    # This folder - project docs
```

## Data Flow

### Config Parsing
```
~/.tmux.conf → parser.py → TmuxConfig {
    keybindings: [Keybinding, ...],
    raw_options: {key: value, ...},
    style: UserStyle {
        prefix_key, uses_vim_keys, prefers_meta, navigation_pattern
    }
}
```

### Suggestion Generation
```
User's TmuxConfig
       ↓
KeybindSuggester.get_suggestions()
       ↓
1. Get curated tips for category
2. Filter out tips user already has
3. Prioritize tips matching user's style
4. Add complementary suggestions (e.g., M-HJKL if user has M-hjkl)
       ↓
List of suggestions displayed as KeybindCards
```

### Sandbox Flow
```
KeybindCard.action_try_keybind()
       ↓
Store keybind in app._keybind_to_try
       ↓
Switch to SandboxScreen
       ↓
User presses 's' → _start_sandbox()
       ↓
1. Load user's ~/.tmux.conf
2. Generate test binding config line
3. Start Docker container with both configs mounted
       ↓
User manually runs: docker exec -it tmux-sandbox tmux attach
       ↓
Practice in container → exit → press 'x' to stop
```

## Key Classes

### TmuxConfig (src/config/models.py)
- Represents parsed tmux configuration
- Contains keybindings, options, and detected style
- Methods: `get_bindings_for_mode()`, `has_binding()`

### KeybindSuggester (src/ai/suggester.py)
- Generates suggestions based on user's config
- Methods: `get_suggestions()` (rule-based), `get_ai_suggestions()` (Claude)

### ContainerManager (src/container/manager.py)
- Manages Docker container lifecycle
- Methods: `start()`, `stop()`, `is_running()`, `get_attach_command()`

### ChallengeEngine (src/challenges/engine.py)
- Runs interactive challenges
- Methods: `start_challenge()`, `check_completion()`, `run_challenge_loop()`

## Environment
- Ubuntu Linux
- Python 3.11+ (via miniconda)
- Docker installed
- ANTHROPIC_API_KEY in ~/.bashrc
- User's terminal: Kitty

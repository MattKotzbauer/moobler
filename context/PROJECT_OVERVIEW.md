# moobler: AI-Powered Tmux Tutor

## Vision
An interactive TUI app that teaches users new tmux keybindings through:
1. AI-powered suggestions based on their existing config and popular GitHub dotfiles
2. Safe containerized sandbox to try new keybindings (with user's real config loaded)
3. Grouped keybindings for cohesive learning (e.g., all resize directions together)
4. One-click integration of approved keybindings into their real config

## Tech Stack
- **Runtime**: Bun (fast JavaScript/TypeScript runtime)
- **Language**: TypeScript
- **TUI**: Ink (React for CLI) with fullscreen alternate buffer
- **AI**: Claude API (Anthropic) for smart suggestions & challenge generation
- **Containers**: Docker + dockerode for isolated tmux sandbox
- **Config**: TypeScript interfaces for parsing and validation

## Current State

### Fully Working
- Ink TUI with 4 screens (Home, Config, Discover, Sandbox)
- Fullscreen mode using alternate screen buffer (like vim/htop)
- Vim-style navigation (j/k/h/l) throughout the app
- Config parser that detects user's style (vim keys, Meta preference, etc.)
- **Smart AI suggestions**: Claude reads user config + scrapes GitHub dotfiles to suggest grouped keybindings
- **User style analysis**: AI explicitly analyzes prefix vs no-prefix preference and matches suggestions
- **Docker sandbox**: Launches in fullscreen Kitty terminal with user's real config + test bindings
- **Pre-warmed containers**: First sandbox launch is instant (container pre-started on app launch)
- Challenge generation (AI creates practice objectives for keybindings)

### Known Limitations
- Progress tracking not implemented
- Challenge validation not automated (user self-validates)
- Config merger (adding keybinds to config) not yet ported to Bun version

---

## Project Structure

```
moobler/
├── package.json            # Bun package config, dependencies, scripts
├── tsconfig.json           # TypeScript configuration
├── bun.lockb               # Bun lockfile
├── base_prompt.txt         # Original project requirements/prompt
├── context/
│   ├── PROJECT_OVERVIEW.md # This file
│   ├── ARCHITECTURE.md     # Technical architecture
│   ├── KEYBINDINGS.md      # App keybinding reference
│   └── ...
├── data/
│   └── curated_tips.json   # Hand-curated tmux tips database
├── docker/
│   ├── Dockerfile          # Sandbox container image (Ubuntu + tmux)
│   └── entrypoint.sh       # Container startup script
└── src/
    ├── index.tsx           # Entry point - fullscreen setup, render App
    ├── app.tsx             # Main App component, routing, global keybindings
    ├── screens/
    │   ├── Home.tsx        # Welcome screen with moobler ASCII art
    │   ├── Config.tsx      # View parsed config, style analysis
    │   ├── Discover.tsx    # AI suggestions, category browser
    │   └── Sandbox.tsx     # Docker sandbox launcher
    └── lib/
        ├── config.ts       # tmux.conf parser, style detection
        ├── ai.ts           # Claude API integration, suggestions
        ├── github.ts       # GitHub dotfiles scraper
        └── docker.ts       # Docker container management
```

---

## File Roles

### `/src/` - Application Source

| File | Role |
|------|------|
| `index.tsx` | Entry point, fullscreen alternate buffer setup, cleanup on exit |
| `app.tsx` | Main App component, screen routing, global keybindings (1-4, q, ?) |
| `screens/Home.tsx` | Welcome screen with moobler ASCII art, config status, menu |
| `screens/Config.tsx` | Display user's keybindings and detected style analysis |
| `screens/Discover.tsx` | Category browser, AI suggestion fetching, keybind selection |
| `screens/Sandbox.tsx` | Docker status, challenge display, Kitty sandbox launcher |
| `lib/config.ts` | Parse ~/.tmux.conf, detect user style (prefix/modifier/nav preferences) |
| `lib/ai.ts` | Claude API wrapper, style-aware suggestion generation |
| `lib/github.ts` | Scrape popular GitHub tmux configs for inspiration |
| `lib/docker.ts` | Docker container management, prewarm, Kitty launch |

### `/docker/` - Container Configuration

| File | Role |
|------|------|
| `Dockerfile` | Ubuntu-based image with tmux, creates `learner` user |
| `entrypoint.sh` | Sets up tmux session on container start |

### `/data/` - Static Data

| File | Role |
|------|------|
| `curated_tips.json` | Hand-picked tmux tips with categories and difficulty |

---

## Key User Flows

### Discovery Flow (Primary)
1. User starts `bun start` → Fullscreen home with moobler ASCII art
2. Press `3` → Discover screen
3. Select category with `j`/`k` on left panel
4. Press Enter or `s` → AI fetches grouped suggestions matching user's style
5. Navigate suggestions with `j`/`k`
6. Press `t` to try in sandbox

### Sandbox Flow
1. From Discover, press `t` on a keybind
2. Sandbox screen shows keybind info and challenge
3. Press `s` → Fullscreen Kitty window opens with:
   - User's existing ~/.tmux.conf loaded
   - New test keybinding appended
   - Challenge description displayed
4. Practice in isolated tmux environment
5. Exit tmux → returns to moobler

---

## Environment Requirements

- Bun 1.0+ (`curl -fsSL https://bun.sh/install | bash`)
- Docker (for sandbox)
- Kitty terminal (for fullscreen sandbox launch)
- ANTHROPIC_API_KEY environment variable (for AI features)

## Running

```bash
# Install dependencies
bun install

# Run
bun start

# Or directly
bun run src/index.tsx

# Development with watch mode
bun dev
```

## Key Bindings (In App)

| Key | Action |
|-----|--------|
| `1-4` | Switch screens (Home/Config/Discover/Sandbox) |
| `j`/`k` | Navigate down/up |
| `h`/`l` | Navigate left/right, switch panels |
| `Enter` | Select/activate |
| `t` | Try keybind in sandbox |
| `s` | Search/Start sandbox |
| `q` | Quit |
| `?` | Show help |
| `m` | Show moobler! (on home screen) |

# Architecture

## Directory Structure
```
moobler/
├── package.json            # Bun config, dependencies, scripts
├── tsconfig.json           # TypeScript config (ESNext, React JSX)
├── bun.lockb               # Bun lockfile
├── src/
│   ├── index.tsx           # Entry point, fullscreen setup
│   ├── app.tsx             # Main App component, routing
│   ├── screens/
│   │   ├── Home.tsx        # Welcome, moobler art, menu
│   │   ├── Config.tsx      # View config, style analysis
│   │   ├── Discover.tsx    # AI suggestions browser
│   │   └── Sandbox.tsx     # Docker sandbox UI
│   └── lib/
│       ├── config.ts       # tmux.conf parsing
│       ├── ai.ts           # Claude API integration
│       ├── github.ts       # GitHub scraper
│       └── docker.ts       # Docker management
├── docker/
│   ├── Dockerfile          # Ubuntu + tmux sandbox image
│   └── entrypoint.sh       # Container setup script
├── data/
│   └── curated_tips.json   # Static tips database
└── context/                # Project documentation
```

## Data Flow

### Config Parsing
```
~/.tmux.conf → lib/config.ts → TmuxConfig {
    keybindings: Keybinding[],
    style: UserStyle {
        prefixPreference: "no-prefix" | "prefix-based" | "mixed",
        modifierPreference: "Alt/Meta" | "Ctrl" | "mixed",
        navigationStyle: "vim" | "arrows" | "other",
        keysInUse: string[]
    },
    raw: string
}
```

### AI Suggestion Generation
```
User's ~/.tmux.conf
       ↓
lib/ai.ts → getAISuggestions(category)
       ↓
1. Read user config, analyze style
2. Scrape GitHub configs for inspiration
3. Send to Claude with style-aware prompt
4. Parse response into KeybindGroup[]
       ↓
SuggestionResult {
    styleAnalysis: { prefixPreference, modifierPreference, ... },
    groups: KeybindGroup[]
}
```

### Sandbox Flow
```
Discover.tsx → tryKeybind(kb)
       ↓
Set keybindToTry in App state
       ↓
Switch to Sandbox.tsx
       ↓
User presses 's' → launchSandbox()
       ↓
1. Write test binding to temp file
2. Build shell script with Docker run command
3. Launch Kitty with fullscreen script
       ↓
User practices in container tmux
       ↓
Exit tmux → Kitty closes → back to moobler
```

## Key Interfaces

### TmuxConfig (lib/config.ts)
```typescript
interface TmuxConfig {
    keybindings: Keybinding[];
    style: UserStyle;
    raw: string;
}

interface Keybinding {
    key: string;
    command: string;
    mode: "prefix" | "root";
    raw: string;
}

interface UserStyle {
    prefixPreference: "no-prefix" | "prefix-based" | "mixed";
    modifierPreference: "Alt/Meta" | "Ctrl" | "mixed";
    navigationStyle: "vim" | "arrows" | "other";
    keysInUse: string[];
}
```

### AI Types (lib/ai.ts)
```typescript
interface KeybindGroup {
    name: string;
    description: string;
    keybinds: KeybindSuggestion[];
    reasoning: string;
}

interface SuggestionResult {
    styleAnalysis: { ... } | null;
    groups: KeybindGroup[];
}
```

## Key Components

### App (app.tsx)
- Main component, manages screen state
- Global keybindings (1-4 for screens, q to quit)
- Passes notify() and tryKeybind() to children
- Triggers container prewarm on mount

### DiscoverScreen (screens/Discover.tsx)
- Two-panel layout: categories (left), suggestions (right)
- Calls getAISuggestions() on category select
- Displays style analysis and grouped suggestions
- t key triggers sandbox with selected keybind

### SandboxScreen (screens/Sandbox.tsx)
- Shows Docker status, selected keybind, challenge
- s key launches Kitty with Docker sandbox
- Generates AI challenge for keybind practice

### lib/docker.ts
- prewarmContainer(): Start container on app launch
- launchSandbox(): Build script, launch in Kitty
- cleanupPrewarm(): Remove container on exit

## Fullscreen Mode

The app uses the terminal's alternate screen buffer:
```typescript
// Enter alternate screen (index.tsx)
process.stdout.write("\x1b[?1049h");  // Enter
process.stdout.write("\x1b[2J");       // Clear
process.stdout.write("\x1b[H");        // Cursor home

// Exit alternate screen (on quit)
process.stdout.write("\x1b[?1049l");
```

This provides a clean, fullscreen experience like vim/htop.

## Environment
- Bun 1.0+ (JavaScript/TypeScript runtime)
- Docker (for sandbox containers)
- Kitty terminal (for fullscreen sandbox)
- ANTHROPIC_API_KEY in environment

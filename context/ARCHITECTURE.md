# Architecture

## Tech Stack
- **Runtime**: Bun 1.0+
- **Language**: TypeScript
- **TUI**: Ink (React for CLI)
- **AI**: Claude API with streaming
- **Containers**: Docker + dockerode

## Directory Structure
```
moobler/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.tsx           # Entry point, fullscreen alt-buffer
│   ├── app.tsx             # Main App, routing, pre-fetch suggestions
│   ├── screens/
│   │   ├── Home.tsx        # ASCII art, menu
│   │   ├── Config.tsx      # View tmux config
│   │   ├── Discover.tsx    # AI suggestions (grouped keybinds)
│   │   └── Sandbox.tsx     # Docker sandbox
│   ├── lib/
│   │   ├── ai.ts           # Claude API, streaming progress
│   │   ├── config.ts       # tmux.conf parser
│   │   ├── docker.ts       # Container management
│   │   └── github.ts       # GitHub scraper
│   └── prompts/
│       ├── suggestions-system.txt
│       ├── suggestions-user.txt
│       └── challenge.txt
├── docker/
│   ├── Dockerfile
│   └── entrypoint.sh
└── context/                # This folder
```

## Key Data Types

```typescript
// A group of related keybinds (e.g., all 4 resize directions)
interface KeybindGroup {
  name: string;           // "Pane Resize"
  description: string;    // "Resize panes with vim keys"
  keybinds: KeybindSuggestion[];  // All related keybinds
  reasoning: string;      // Why grouped together
}

interface SuggestionResult {
  styleAnalysis: { ... } | null;
  groups: KeybindGroup[];  // Groups are the selectable units
}
```

## Key Flows

### App Startup
1. Enter alt-screen buffer (fullscreen)
2. Start Docker prewarm
3. Start AI prefetch (getAISuggestions with streaming progress)
4. Show Home screen

### Discover Screen
- Left panel: categories
- Right panel: AI suggestions grouped by functionality
- Selection should be per-GROUP (not per-keybind)
- Pressing 't' sends entire group to sandbox

### Sandbox
- Launches Kitty terminal with Docker container
- Mounts user's tmux.conf + test bindings
- All keybinds in a group are added together

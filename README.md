# moobler

WIP AI tmux tutor - addressing the green lumber problem ("can't describe how to ride a bike") in devtooling

```
         /( ,,,,, )\
        _\,;;;;;;;,/_
     .-"; ;;;;;;;;; ;"-.
     '.__/`_ / \ _`\__.'
        | (')| |(') |
        | .--' '--. |
        |/ o     o \|
        |           |
       / \ _..=.._ / \
      /:. '._____.'   \
     ;::'    / \      .;
     |     _|_ _|_   ::|
   .-|     '==o=='    '|-.
  /  |  . /       \    |  \
  |  | ::|         |   | .|
  |  (  ')         (.  )::|
  |: |   |; U U U ;|:: | `|
  |' |   | \ U U / |'  |  |
  ##V|   |_/`"""`\_|   |V##
     ##V##         ##V##
```

moo

## What is this?

An interactive TUI that helps you learn and discover tmux keybindings:

- **Discover**: AI analyzes your `~/.tmux.conf` and suggests new keybindings that match your style
- **Sandbox**: Practice keybindings in a safe Docker container
- **Config**: View your current tmux configuration

## Requirements

- [Bun](https://bun.sh/) runtime
- [Docker](https://www.docker.com/) for the sandbox
- [Kitty](https://sw.kovidgoyal.net/kitty/) terminal (for sandbox - more terminals coming soon)
- `ANTHROPIC_API_KEY` environment variable for AI suggestions

## Install & Run

```bash
# Clone and install
git clone https://github.com/yourusername/moobler.git
cd moobler
bun install

# Run
ANTHROPIC_API_KEY=your_key bun run src/index.tsx
```

## Controls

| Key | Action |
|-----|--------|
| `1` | Home screen |
| `2` | View config |
| `3` | Discover new keybindings |
| `4` | Sandbox |
| `q` | Quit |
| `?` | Help |

## Status

Work in progress. Currently supports:
- [x] AI-powered keybinding suggestions
- [x] Style analysis (detects your prefix/modifier preferences)
- [x] Docker sandbox for practicing
- [ ] Multi-terminal support (kitty only for now)
- [ ] Keybinding challenges/tutorials

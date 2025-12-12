# TODO / Next Steps

## Priority 1: Claude AI Integration

### Current State
- `src/ai/client.py` has ClaudeClient with methods:
  - `analyze_config()` - Send config to Claude, get style analysis
  - `suggest_keybinds()` - Generate personalized suggestions
  - `generate_challenge()` - Create learning challenges
- `src/ai/suggester.py` has `get_ai_suggestions()` ready
- ANTHROPIC_API_KEY is available in environment

### To Do
1. Wire "Search Online" button in discover.py to call Claude
2. Add loading indicator while Claude generates suggestions
3. Display AI suggestions alongside curated ones
4. Use Claude to generate dynamic challenges for any keybind

### Implementation Notes
```python
# In discover.py, add to on_button_pressed:
elif event.button.id == "btn-search":
    self.run_worker(self._fetch_ai_suggestions())

async def _fetch_ai_suggestions(self):
    self.query_one("#loading").display = True
    try:
        from ...ai.client import ClaudeClient
        client = ClaudeClient()  # Uses ANTHROPIC_API_KEY from env
        suggestions = await client.suggest_keybinds(
            user_style=self._user_config.style.model_dump(),
            existing_bindings=[kb.key_combo for kb in self._user_config.keybindings],
            category=self._current_category,
        )
        # Display suggestions...
    finally:
        self.query_one("#loading").display = False
```

## Priority 2: Sandbox UX

### Problem
User has to manually open another terminal and run docker exec command.
Especially awkward when running inside tmux (tmux-in-tmux).

### Options Considered
1. **Auto-split tmux pane** - Works when user is in tmux
2. **Spawn new terminal (kitty)** - Works in any context
3. **Embed terminal in TUI** - Complex, may not work well

### Recommended: Detect context and act accordingly
```python
def launch_sandbox():
    if os.environ.get("TMUX"):
        # Inside tmux: split pane
        os.system(f'tmux split-window -h "docker exec -it tmux-sandbox tmux attach; read"')
    elif shutil.which("kitty"):
        # Kitty terminal available
        os.system(f'kitty --hold docker exec -it tmux-sandbox tmux attach')
    else:
        # Fallback: show command to copy
        show_manual_instructions()
```

### To Do
1. Add terminal detection in sandbox.py
2. Implement auto-launch for tmux context
3. Implement auto-launch for kitty
4. Keep manual fallback for other terminals

## Priority 3: Challenge System

### Current State
- `src/challenges/types.py` defines Challenge model and BUILTIN_CHALLENGES
- `src/challenges/engine.py` has ChallengeEngine
- `src/ai/challenge_gen.py` can generate challenges via Claude

### To Do
1. Create Challenge UI screen
2. Wire challenge engine to sandbox
3. Have Claude generate challenges for any keybind:
   ```python
   challenge = await client.generate_challenge(
       keybind="M-H",
       command="resize-pane -L 5",
       difficulty="beginner"
   )
   # Returns: {objective, setup, expected_keys, success_criteria, hint}
   ```
4. Display challenge objective in sandbox
5. Validate completion (check pane moved, etc.)

## Priority 4: Config Merger

### Current State
- `src/config/merger.py` has ConfigMerger class
- Methods: `add_keybinding()`, `backup_config()`, `restore_backup()`

### To Do
1. Wire "Add to Config" button to ConfigMerger
2. Show confirmation before modifying ~/.tmux.conf
3. Auto-backup before any modification
4. Show diff of what will be added
5. Offer to reload tmux config after adding

## Future Ideas
- GitHub scraper to find popular configs
- Spaced repetition for practicing keybinds
- Progress tracking / gamification
- Share configs / export learned keybinds
- Plugin recommendations (tpm, tmux-resurrect, etc.)

# Claude AI Integration Plan

## Available API Key
- `ANTHROPIC_API_KEY` is set in `~/.bashrc`
- Starts with `sk-ant-api...`

## Current Infrastructure

### ClaudeClient (src/ai/client.py)
```python
class ClaudeClient:
    def __init__(self, api_key=None):
        # Uses ANTHROPIC_API_KEY from env if not provided
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    async def analyze_config(self, config_content: str) -> dict:
        """Analyze tmux config, return style insights."""
        # Returns: {style_summary, notable_bindings, patterns, suggestions}

    async def suggest_keybinds(self, user_style, existing_bindings, category) -> list:
        """Generate personalized keybind suggestions."""
        # Returns: [{keybind, command, description, reasoning}, ...]

    async def generate_challenge(self, keybind, command, difficulty) -> dict:
        """Create interactive learning challenge."""
        # Returns: {objective, setup, expected_keys, success_criteria, hint}
```

### KeybindSuggester (src/ai/suggester.py)
```python
class KeybindSuggester:
    async def get_ai_suggestions(self, config, category) -> list:
        """Get AI-powered suggestions using Claude."""
        # Calls client.suggest_keybinds() with user's style
```

### ChallengeGenerator (src/ai/challenge_gen.py)
```python
class ChallengeGenerator:
    async def generate_for_keybind(self, keybind, command, difficulty) -> dict:
        """Generate challenge via Claude or fall back to templates."""
```

## Integration Points

### 1. Discover Screen - "Search Online" Button
**File**: `src/ui/screens/discover.py`
**Location**: `on_button_pressed()` method

```python
elif event.button.id == "btn-search":
    self.run_worker(self._fetch_ai_suggestions())

async def _fetch_ai_suggestions(self):
    """Fetch suggestions from Claude based on user's config."""
    loading = self.query_one("#loading")
    loading.display = True

    try:
        from ...ai.client import ClaudeClient
        client = ClaudeClient()

        # Get user's style and existing bindings
        style = self._user_config.style.model_dump() if self._user_config else {}
        existing = [kb.key_combo for kb in self._user_config.keybindings] if self._user_config else []

        # Call Claude
        suggestions = await client.suggest_keybinds(
            user_style=style,
            existing_bindings=existing,
            category=self._current_category,
        )

        # Display suggestions
        container = self.query_one("#suggestion-list")
        for s in suggestions:
            card = KeybindCard(
                keybind=s.get("keybind", ""),
                description=f"[AI] {s.get('description', '')}",
                command=s.get("command", ""),
            )
            container.mount(card)

    except Exception as e:
        self.app.notify(f"Error: {e}", title="AI Search Failed")
    finally:
        loading.display = False
```

### 2. Challenge Generation
**File**: `src/ui/screens/sandbox.py`

When user tries a keybind, generate a challenge:
```python
async def _generate_challenge(self):
    """Generate a challenge for the current keybind using Claude."""
    if not self._keybind_to_try:
        return None

    from ...ai.challenge_gen import ChallengeGenerator
    generator = ChallengeGenerator(ClaudeClient())

    challenge = await generator.generate_for_keybind(
        keybind=self._keybind_to_try["keybind"],
        command=self._keybind_to_try["command"],
        difficulty="beginner",
    )

    return challenge
    # Returns: {objective, setup, expected_keys, success_criteria, hint}
```

### 3. Config Analysis
**File**: `src/ui/screens/config_view.py`

Add "Analyze with AI" button:
```python
async def _analyze_with_ai(self):
    """Have Claude analyze the user's config."""
    client = ClaudeClient()
    config_content = Path.home().joinpath(".tmux.conf").read_text()

    analysis = await client.analyze_config(config_content)
    # Display: style_summary, notable_bindings, patterns, suggestions
```

## Claude Prompts Used

### suggest_keybinds system prompt:
```
You are a tmux expert helping users discover new keybindings.
Given the user's style and existing bindings, suggest complementary keybindings that:
1. Match their style (vim keys, arrow keys, modifier preferences)
2. Don't conflict with existing bindings
3. Are genuinely useful for productivity
4. Have clear mnemonics or patterns

Respond in JSON format as a list of objects with: keybind, command, description, reasoning
```

### generate_challenge system prompt:
```
You are creating interactive tmux learning challenges.
Create a mini-challenge that helps users practice and remember a keybinding.

The challenge should have:
1. A clear objective
2. A starting state (how many panes, what's in them)
3. Expected actions the user should take
4. Success criteria
5. A hint if they get stuck

Respond in JSON with: objective, setup, expected_keys, success_criteria, hint
```

## Error Handling
- If ANTHROPIC_API_KEY not set: Show error, fall back to curated tips
- If API call fails: Show error notification, don't crash
- If response parsing fails: Log raw response, show generic error

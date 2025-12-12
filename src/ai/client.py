"""Claude API client wrapper."""

import os
from typing import Optional

from anthropic import Anthropic
from pydantic import BaseModel


class ClaudeClient:
    """Wrapper for Claude API interactions."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Claude client.

        Args:
            api_key: Anthropic API key. If not provided, uses ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    async def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> str:
        """Get a completion from Claude.

        Args:
            prompt: The user prompt
            system: Optional system prompt
            max_tokens: Maximum tokens in response

        Returns:
            Claude's response text
        """
        messages = [{"role": "user", "content": prompt}]

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or "",
            messages=messages,
        )

        return response.content[0].text

    async def analyze_config(self, config_content: str) -> dict:
        """Analyze a tmux configuration and return insights.

        Args:
            config_content: The tmux.conf content

        Returns:
            Dict with analysis results
        """
        system = """You are a tmux expert. Analyze the given tmux configuration and provide:
1. A summary of the user's style (vim vs arrow keys, prefix choice, etc.)
2. Notable keybindings they have
3. Common patterns they follow
4. Gaps or missing essential keybindings

Respond in JSON format with keys: style_summary, notable_bindings, patterns, suggestions"""

        prompt = f"""Analyze this tmux configuration:

```
{config_content}
```

Provide your analysis in JSON format."""

        response = await self.complete(prompt, system=system, max_tokens=2048)
        # Parse JSON from response (handle markdown code blocks)
        import json
        import re

        # Extract JSON from markdown code block if present
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            response = json_match.group(1)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response}

    async def suggest_keybinds(
        self,
        user_style: dict,
        existing_bindings: list[str],
        category: Optional[str] = None,
    ) -> list[dict]:
        """Suggest new keybindings based on user's style.

        Args:
            user_style: Dict describing user's keybinding style
            existing_bindings: List of user's current keybindings
            category: Optional category to focus suggestions on

        Returns:
            List of suggested keybindings
        """
        system = """You are a tmux expert helping users discover new keybindings.
Given the user's style and existing bindings, suggest complementary keybindings that:
1. Match their style (vim keys, arrow keys, modifier preferences)
2. Don't conflict with existing bindings
3. Are genuinely useful for productivity
4. Have clear mnemonics or patterns

Respond in JSON format as a list of objects with: keybind, command, description, reasoning"""

        category_focus = f"\nFocus on {category} keybindings." if category else ""

        prompt = f"""User's style: {user_style}

Existing bindings: {existing_bindings}
{category_focus}

Suggest 5 new keybindings that would complement their setup. Respond in JSON format."""

        response = await self.complete(prompt, system=system, max_tokens=2048)

        import json
        import re

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            response = json_match.group(1)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []

    async def generate_challenge(
        self,
        keybind: str,
        command: str,
        difficulty: str = "beginner",
    ) -> dict:
        """Generate an interactive challenge for learning a keybinding.

        Args:
            keybind: The keybind to learn
            command: The tmux command it executes
            difficulty: Challenge difficulty level

        Returns:
            Challenge definition dict
        """
        system = """You are creating interactive tmux learning challenges.
Create a mini-challenge that helps users practice and remember a keybinding.

The challenge should have:
1. A clear objective
2. A starting state (how many panes, what's in them)
3. Expected actions the user should take
4. Success criteria
5. A hint if they get stuck

Respond in JSON with: objective, setup, expected_keys, success_criteria, hint"""

        prompt = f"""Create a {difficulty} challenge for learning:
Keybind: {keybind}
Command: {command}

The challenge should help them understand what this keybind does and practice using it.
Respond in JSON format."""

        response = await self.complete(prompt, system=system, max_tokens=1024)

        import json
        import re

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            response = json_match.group(1)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response}

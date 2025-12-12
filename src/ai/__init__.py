"""AI module for Claude-powered suggestions."""

from .client import ClaudeClient
from .suggester import KeybindSuggester

__all__ = ["ClaudeClient", "KeybindSuggester"]

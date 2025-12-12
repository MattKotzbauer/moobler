"""Discovery module for finding new tmux configurations."""

from .curated import get_curated_tips, CuratedTip
from .github_scraper import scrape_github_dotfiles

__all__ = ["get_curated_tips", "CuratedTip", "scrape_github_dotfiles"]

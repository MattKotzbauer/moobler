"""Merge new keybindings into existing tmux configuration."""

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Keybinding, BindingMode


class ConfigMerger:
    """Merge new keybindings into tmux configuration."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the merger.

        Args:
            config_path: Path to tmux.conf. Defaults to ~/.tmux.conf
        """
        self.config_path = config_path or Path.home() / ".tmux.conf"
        self.backup_dir = Path.home() / ".local" / "share" / "tmux-learn" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_config(self) -> Path:
        """Create a backup of the current config.

        Returns:
            Path to the backup file
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"tmux.conf.{timestamp}.bak"
        shutil.copy2(self.config_path, backup_path)

        return backup_path

    def restore_backup(self, backup_path: Path) -> None:
        """Restore a backup.

        Args:
            backup_path: Path to the backup file
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        shutil.copy2(backup_path, self.config_path)

    def list_backups(self) -> list[Path]:
        """List all available backups.

        Returns:
            List of backup file paths, newest first
        """
        backups = list(self.backup_dir.glob("tmux.conf.*.bak"))
        return sorted(backups, reverse=True)

    def format_binding(
        self,
        keybind: str,
        command: str,
        description: Optional[str] = None,
        mode: BindingMode = BindingMode.PREFIX,
    ) -> str:
        """Format a keybinding as a tmux config line.

        Args:
            keybind: The key combination (e.g., "M-h", "h")
            command: The tmux command
            description: Optional description for comment
            mode: Binding mode

        Returns:
            Formatted config line(s)
        """
        lines = []

        if description:
            lines.append(f"# {description}")

        # Determine bind command format
        if mode == BindingMode.ROOT:
            lines.append(f"bind -n {keybind} {command}")
        elif mode == BindingMode.COPY_MODE_VI:
            lines.append(f"bind -T copy-mode-vi {keybind} {command}")
        elif mode == BindingMode.COPY_MODE:
            lines.append(f"bind -T copy-mode {keybind} {command}")
        else:
            lines.append(f"bind {keybind} {command}")

        return "\n".join(lines)

    def find_section(self, content: str, category: str) -> Optional[int]:
        """Find the line number where a category section starts.

        Args:
            content: Config file content
            category: Category to find (e.g., "navigation", "panes")

        Returns:
            Line number or None if not found
        """
        patterns = [
            rf"#.*{category}.*keybind",
            rf"#.*{category}.*bind",
            rf"#.*{category}",
        ]

        lines = content.splitlines()
        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    return i

        return None

    def add_keybinding(
        self,
        keybind: str,
        command: str,
        description: Optional[str] = None,
        mode: BindingMode = BindingMode.PREFIX,
        category: Optional[str] = None,
        create_backup: bool = True,
    ) -> tuple[bool, str]:
        """Add a new keybinding to the config.

        Args:
            keybind: The key combination
            command: The tmux command
            description: Optional description
            mode: Binding mode
            category: Optional category for placement
            create_backup: Whether to backup before modifying

        Returns:
            Tuple of (success, message)
        """
        # Create config if it doesn't exist
        if not self.config_path.exists():
            self.config_path.write_text("# tmux configuration\n\n")

        # Backup
        if create_backup:
            backup_path = self.backup_config()

        content = self.config_path.read_text()

        # Check if binding already exists
        if self._binding_exists(content, keybind, mode):
            return False, f"Binding for {keybind} already exists"

        # Format the new binding
        new_binding = self.format_binding(keybind, command, description, mode)

        # Find appropriate location
        lines = content.splitlines()
        insert_at = len(lines)  # Default to end

        if category:
            section_line = self.find_section(content, category)
            if section_line is not None:
                # Find the end of this section (next section or end)
                for i in range(section_line + 1, len(lines)):
                    if lines[i].startswith("# ") and not lines[i].startswith("# " + category[0]):
                        insert_at = i
                        break
                else:
                    insert_at = len(lines)
            else:
                # Add category header
                new_binding = f"\n# {category.title()} keybindings\n{new_binding}"

        # Insert the binding
        lines.insert(insert_at, new_binding)

        # Write back
        self.config_path.write_text("\n".join(lines))

        msg = f"Added binding: {keybind} -> {command}"
        if create_backup:
            msg += f" (backup: {backup_path.name})"

        return True, msg

    def _binding_exists(self, content: str, keybind: str, mode: BindingMode) -> bool:
        """Check if a binding already exists in the config."""
        # Escape special regex characters in keybind
        escaped_key = re.escape(keybind)

        if mode == BindingMode.ROOT:
            pattern = rf"^\s*bind(?:-key)?\s+-n\s+{escaped_key}\s+"
        elif mode in (BindingMode.COPY_MODE, BindingMode.COPY_MODE_VI):
            pattern = rf"^\s*bind(?:-key)?\s+-T\s+{mode.value}\s+{escaped_key}\s+"
        else:
            pattern = rf"^\s*bind(?:-key)?\s+{escaped_key}\s+"

        return bool(re.search(pattern, content, re.MULTILINE))

    def add_multiple_keybindings(
        self,
        bindings: list[dict],
        create_backup: bool = True,
    ) -> list[tuple[str, bool, str]]:
        """Add multiple keybindings at once.

        Args:
            bindings: List of binding dicts with keys: keybind, command, description, mode, category
            create_backup: Whether to backup before modifying

        Returns:
            List of (keybind, success, message) tuples
        """
        if create_backup and self.config_path.exists():
            self.backup_config()

        results = []
        for binding in bindings:
            keybind = binding["keybind"]
            command = binding["command"]
            description = binding.get("description")
            mode = binding.get("mode", BindingMode.PREFIX)
            category = binding.get("category")

            success, msg = self.add_keybinding(
                keybind=keybind,
                command=command,
                description=description,
                mode=mode,
                category=category,
                create_backup=False,  # Already backed up
            )
            results.append((keybind, success, msg))

        return results

    def remove_keybinding(
        self,
        keybind: str,
        mode: BindingMode = BindingMode.PREFIX,
        create_backup: bool = True,
    ) -> tuple[bool, str]:
        """Remove a keybinding from the config.

        Args:
            keybind: The key combination to remove
            mode: Binding mode
            create_backup: Whether to backup before modifying

        Returns:
            Tuple of (success, message)
        """
        if not self.config_path.exists():
            return False, "Config file not found"

        if create_backup:
            self.backup_config()

        content = self.config_path.read_text()
        escaped_key = re.escape(keybind)

        if mode == BindingMode.ROOT:
            pattern = rf"^.*bind(?:-key)?\s+-n\s+{escaped_key}\s+.*$"
        elif mode in (BindingMode.COPY_MODE, BindingMode.COPY_MODE_VI):
            pattern = rf"^.*bind(?:-key)?\s+-T\s+{mode.value}\s+{escaped_key}\s+.*$"
        else:
            pattern = rf"^.*bind(?:-key)?\s+{escaped_key}\s+.*$"

        new_content, count = re.subn(pattern, "", content, flags=re.MULTILINE)

        if count == 0:
            return False, f"Binding for {keybind} not found"

        # Clean up empty lines
        new_content = re.sub(r"\n{3,}", "\n\n", new_content)
        self.config_path.write_text(new_content)

        return True, f"Removed binding for {keybind}"

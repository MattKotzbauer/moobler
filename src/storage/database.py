"""SQLite database management."""

import aiosqlite
from pathlib import Path
from typing import Optional


class Database:
    """SQLite database for persistent storage."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the database.

        Args:
            db_path: Path to SQLite database file.
                    Defaults to ~/.local/share/tmux-learn/data.db
        """
        if db_path is None:
            data_dir = Path.home() / ".local" / "share" / "tmux-learn"
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "data.db"

        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Connect to the database."""
        self._connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        assert self._connection is not None

        await self._connection.executescript("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS completed_challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenge_id TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_taken REAL,
                attempts INTEGER DEFAULT 1,
                UNIQUE(challenge_id)
            );

            CREATE TABLE IF NOT EXISTS learned_keybinds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keybind TEXT NOT NULL,
                command TEXT NOT NULL,
                description TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                integrated BOOLEAN DEFAULT FALSE,
                UNIQUE(keybind)
            );

            CREATE TABLE IF NOT EXISTS practice_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keybind TEXT NOT NULL,
                practiced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE
            );

            CREATE INDEX IF NOT EXISTS idx_practice_keybind ON practice_history(keybind);
            CREATE INDEX IF NOT EXISTS idx_practice_date ON practice_history(practiced_at);
        """)
        await self._connection.commit()

    @property
    def connection(self) -> aiosqlite.Connection:
        """Get the database connection."""
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    # Preferences
    async def set_preference(self, key: str, value: str) -> None:
        """Set a user preference."""
        await self.connection.execute(
            """
            INSERT INTO user_preferences (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value=?, updated_at=CURRENT_TIMESTAMP
            """,
            (key, value, value),
        )
        await self.connection.commit()

    async def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a user preference."""
        async with self.connection.execute(
            "SELECT value FROM user_preferences WHERE key = ?", (key,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else default

    # Challenges
    async def mark_challenge_completed(
        self,
        challenge_id: str,
        time_taken: float,
        attempts: int,
    ) -> None:
        """Mark a challenge as completed."""
        await self.connection.execute(
            """
            INSERT INTO completed_challenges (challenge_id, time_taken, attempts)
            VALUES (?, ?, ?)
            ON CONFLICT(challenge_id) DO UPDATE SET
                time_taken = MIN(time_taken, ?),
                attempts = ?
            """,
            (challenge_id, time_taken, attempts, time_taken, attempts),
        )
        await self.connection.commit()

    async def is_challenge_completed(self, challenge_id: str) -> bool:
        """Check if a challenge has been completed."""
        async with self.connection.execute(
            "SELECT 1 FROM completed_challenges WHERE challenge_id = ?",
            (challenge_id,),
        ) as cursor:
            return await cursor.fetchone() is not None

    async def get_completed_challenges(self) -> list[dict]:
        """Get all completed challenges."""
        async with self.connection.execute(
            """
            SELECT challenge_id, completed_at, time_taken, attempts
            FROM completed_challenges
            ORDER BY completed_at DESC
            """
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "challenge_id": row[0],
                    "completed_at": row[1],
                    "time_taken": row[2],
                    "attempts": row[3],
                }
                for row in rows
            ]

    # Keybinds
    async def add_learned_keybind(
        self,
        keybind: str,
        command: str,
        description: Optional[str] = None,
    ) -> None:
        """Add a keybind to the learned list."""
        await self.connection.execute(
            """
            INSERT INTO learned_keybinds (keybind, command, description)
            VALUES (?, ?, ?)
            ON CONFLICT(keybind) DO UPDATE SET
                command = ?,
                description = ?
            """,
            (keybind, command, description, command, description),
        )
        await self.connection.commit()

    async def mark_keybind_integrated(self, keybind: str) -> None:
        """Mark a keybind as integrated into the user's config."""
        await self.connection.execute(
            "UPDATE learned_keybinds SET integrated = TRUE WHERE keybind = ?",
            (keybind,),
        )
        await self.connection.commit()

    async def get_learned_keybinds(self, integrated_only: bool = False) -> list[dict]:
        """Get learned keybinds."""
        query = "SELECT keybind, command, description, added_at, integrated FROM learned_keybinds"
        if integrated_only:
            query += " WHERE integrated = TRUE"
        query += " ORDER BY added_at DESC"

        async with self.connection.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    "keybind": row[0],
                    "command": row[1],
                    "description": row[2],
                    "added_at": row[3],
                    "integrated": row[4],
                }
                for row in rows
            ]

    # Practice history
    async def log_practice(self, keybind: str, success: bool = True) -> None:
        """Log a practice attempt."""
        await self.connection.execute(
            "INSERT INTO practice_history (keybind, success) VALUES (?, ?)",
            (keybind, success),
        )
        await self.connection.commit()

    async def get_practice_stats(self, keybind: Optional[str] = None) -> dict:
        """Get practice statistics."""
        if keybind:
            async with self.connection.execute(
                """
                SELECT COUNT(*), SUM(CASE WHEN success THEN 1 ELSE 0 END)
                FROM practice_history WHERE keybind = ?
                """,
                (keybind,),
            ) as cursor:
                row = await cursor.fetchone()
                total = row[0] or 0
                successes = row[1] or 0
                return {
                    "keybind": keybind,
                    "total_attempts": total,
                    "successful": successes,
                    "success_rate": successes / total if total > 0 else 0,
                }
        else:
            async with self.connection.execute(
                """
                SELECT keybind, COUNT(*), SUM(CASE WHEN success THEN 1 ELSE 0 END)
                FROM practice_history
                GROUP BY keybind
                """
            ) as cursor:
                rows = await cursor.fetchall()
                return {
                    row[0]: {
                        "total_attempts": row[1],
                        "successful": row[2],
                        "success_rate": row[2] / row[1] if row[1] > 0 else 0,
                    }
                    for row in rows
                }

    async def get_overall_progress(self) -> dict:
        """Get overall learning progress."""
        # Count completed challenges
        async with self.connection.execute(
            "SELECT COUNT(*) FROM completed_challenges"
        ) as cursor:
            completed_challenges = (await cursor.fetchone())[0]

        # Count learned keybinds
        async with self.connection.execute(
            "SELECT COUNT(*), SUM(CASE WHEN integrated THEN 1 ELSE 0 END) FROM learned_keybinds"
        ) as cursor:
            row = await cursor.fetchone()
            learned_keybinds = row[0]
            integrated_keybinds = row[1] or 0

        # Total practice sessions
        async with self.connection.execute(
            "SELECT COUNT(*) FROM practice_history"
        ) as cursor:
            total_practice = (await cursor.fetchone())[0]

        return {
            "completed_challenges": completed_challenges,
            "learned_keybinds": learned_keybinds,
            "integrated_keybinds": integrated_keybinds,
            "total_practice_sessions": total_practice,
        }
